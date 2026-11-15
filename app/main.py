import asyncio
import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from app.config import settings
from app.job_manager import JobManager, JobStatus
from app.audio import extract_audio
from app.transcription import WhisperEngine

settings.ensure_directories()
app = FastAPI(title=settings.APP_NAME)
job_manager = JobManager(base_dir=settings.JOBS_DIR)

def run_transcription_pipeline(
    job_id: str,
    source_path: Path,
    model_size: str,
    initial_prompt: str | None
) -> None:
    job = job_manager.get_job(job_id)
    if not job:
        return
    job_dir = job["job_dir"]
    audio_path = job_dir / "extracted_audio.wav"

    try:
        job_manager.update_status(job_id, JobStatus.EXTRACTING)
        duration = extract_audio(source_path, audio_path)
        job_manager.update_progress(job_id, 0.0, 0.0, duration)

        # Remove raw video upload to immediately recover disk space
        if source_path.exists():
            try:
                source_path.unlink()
            except OSError:
                pass

        job_manager.update_status(job_id, JobStatus.TRANSCRIBING)
        engine = WhisperEngine(model_name=model_size, cpu_threads=settings.CPU_THREADS)

        segments = []
        for seg, info in engine.transcribe(audio_path, initial_prompt=initial_prompt):
            segments.append(seg)
            if duration > 0:
                progress = min(100.0, (seg["end"] / duration) * 100.0)
                job_manager.update_progress(job_id, progress, seg["end"], duration)

        job_manager.complete_job(job_id, segments)

    except Exception as e:
        job_manager.update_status(job_id, JobStatus.FAILED, error=str(e))

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}

@app.post("/api/jobs", status_code=202)
async def create_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    model_size: str = Form("small"),
    initial_prompt: str = Form(None)
):
    if model_size not in settings.SUPPORTED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model: {model_size}. Supported: {settings.SUPPORTED_MODELS}"
        )

    clean_filename = file.filename or "upload.mp4"
    job_id = job_manager.create_job(
        filename=clean_filename,
        model_size=model_size,
        initial_prompt=initial_prompt
    )
    job = job_manager.get_job(job_id)
    job_dir: Path = job["job_dir"]
    source_path = job_dir / f"source_{clean_filename}"

    # Stream file to disk in 1MB chunks to keep RAM usage minimal
    with open(source_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            f.write(chunk)

    background_tasks.add_task(
        run_transcription_pipeline,
        job_id=job_id,
        source_path=source_path,
        model_size=model_size,
        initial_prompt=initial_prompt
    )

    return {"job_id": job_id, "status": JobStatus.QUEUED}

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job["job_id"],
        "filename": job["filename"],
        "model_size": job["model_size"],
        "status": job["status"],
        "progress": job["progress"],
        "current_time": job["current_time"],
        "total_duration": job["total_duration"],
        "error": job["error"],
        "preview": job.get("preview")
    }

@app.get("/api/jobs/{job_id}/download/{fmt}")
def download_transcript(job_id: str, fmt: str):
    job = job_manager.get_job(job_id)
    if not job or job["status"] != JobStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Completed transcript not found")
    if fmt not in ["txt", "srt", "vtt"]:
        raise HTTPException(status_code=400, detail="Invalid format. Choose txt, srt, or vtt")

    file_path = job["files"].get(fmt)
    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail=f"{fmt.upper()} file missing")

    stem = Path(job["filename"]).stem
    return FileResponse(
        str(file_path),
        filename=f"{stem}.{fmt}",
        media_type="text/plain; charset=utf-8"
    )

@app.get("/api/jobs/{job_id}/events")
async def job_events(job_id: str):
    async def event_generator():
        while True:
            job = job_manager.get_job(job_id)
            if not job:
                yield {"event": "error", "data": json.dumps({"error": "Job not found"})}
                break

            payload = {
                "job_id": job["job_id"],
                "status": job["status"],
                "progress": job["progress"],
                "current_time": job["current_time"],
                "total_duration": job["total_duration"],
                "error": job["error"]
            }
            yield {"event": "update", "data": json.dumps(payload)}

            if job["status"] in [JobStatus.COMPLETED, JobStatus.FAILED]:
                break
            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())

# Mount embedded web frontend if static directory exists
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
