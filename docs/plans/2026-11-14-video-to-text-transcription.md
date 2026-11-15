# Video to Text Transcription Service Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Build a lightweight, local REST API microservice and embedded drag-and-drop web UI that extracts audio from large video files (up to 3.7 GB+) and transcribes them into `.txt` (formatted for Google NotebookLM), `.srt`, and `.vtt` subtitles using `faster-whisper` on CPU.

**Architecture:** A FastAPI backend coordinates streaming file uploads, executes background jobs via a thread pool, extracts 16 kHz mono audio using FFmpeg, and transcribes audio segments with `faster-whisper` INT8 quantization while pushing real-time progress events to a single-page HTML5/JS frontend.

**Tech Stack:** Python 3.11, FastAPI, Uvicorn, faster-whisper (CTranslate2), FFmpeg, Server-Sent Events (SSE), HTML5, Tailwind CSS, Vanilla JavaScript, pytest.

---

## Multi-Session Checkpoint Tracker

Use this checklist to track progress across sessions without losing context or wasting tokens:

### Session 1: Foundations & Extraction
- [ ] **Task 1: Environment & Project Configuration** (Settings, directories, requirements)
- [ ] **Task 2: Subtitle & Transcript Formatters** (`.txt`, `.srt`, `.vtt` formatting)
- [ ] **Task 3: FFmpeg Audio Extraction & Probing** (Audio stripping & duration probe)
*Session 1 Checkpoint: All unit tests pass, commit & push to GitHub.*

### Session 2: Transcription Engine & Job Queue
- [ ] **Task 4: faster-whisper Model Wrapper** (INT8 CPU inference & segment streaming)
- [ ] **Task 5: Job Manager & Task Queue** (Lifecycle state machine & scratch file management)
*Session 2 Checkpoint: Mocked engine and queue tests pass, commit & push to GitHub.*

### Session 3: REST API & Streaming Endpoints
- [ ] **Task 6: FastAPI Application & Endpoints** (Streaming upload, SSE progress events, download routes)
*Session 3 Checkpoint: API integration tests pass, commit & push to GitHub.*

### Session 4: Web UI & End-to-End Verification
- [ ] **Task 7: Drag-and-Drop Web UI** (HTML5, Tailwind, live progress bar, NotebookLM copy button)
- [ ] **Task 8: CLI Runner & End-to-End Verification** (`run.py`, synthetic audio verification test)
*Session 4 Checkpoint: Full test suite passes, live browser smoke test, ready for merge.*

---

### Task 1: Environment & Project Configuration

**Files:**
- Create: `requirements.txt`
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `tests/__init__.py`
- Test: `tests/test_config.py`

**Step 1: Write failing test**
Create `tests/test_config.py`:
```python
import os
from pathlib import Path
from app.config import Settings

def test_default_settings():
    settings = Settings()
    assert settings.CPU_THREADS >= 1
    assert "small" in settings.SUPPORTED_MODELS
    assert settings.DEFAULT_MODEL == "small"
    assert isinstance(settings.DATA_DIR, Path)
    assert isinstance(settings.UPLOAD_DIR, Path)
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_config.py`  
Expected: FAIL (ModuleNotFoundError: No module named 'app')

**Step 3: Write minimal implementation**
Create `requirements.txt`:
```text
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
python-multipart>=0.0.9
faster-whisper>=1.0.0
sse-starlette>=2.0.0
pydantic>=2.0.0
pytest>=8.0.0
httpx>=0.27.0
```

Create `app/__init__.py` (empty file).  
Create `tests/__init__.py` (empty file).  
Create `app/config.py`:
```python
from pathlib import Path
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "Video-to-Text Transcriber"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CPU_THREADS: int = 6
    DEFAULT_MODEL: str = "small"
    SUPPORTED_MODELS: list[str] = ["base", "small", "medium", "large-v3"]
    DATA_DIR: Path = Path("data")
    UPLOAD_DIR: Path = Path("data/uploads")
    JOBS_DIR: Path = Path("data/jobs")
    MODELS_DIR: Path = Path("models")

    def ensure_directories(self) -> None:
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.JOBS_DIR.mkdir(parents=True, exist_ok=True)
        self.MODELS_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
```

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_config.py`  
Expected: PASS

**Step 5: Commit**
```bash
git add requirements.txt app/__init__.py app/config.py tests/__init__.py tests/test_config.py
git commit -m "feat(config): add settings and directory structure"
```

---

### Task 2: Subtitle & Transcript Formatters (.txt, .srt, .vtt)

**Files:**
- Create: `app/formatter.py`
- Test: `tests/test_formatter.py`

**Step 1: Write failing test**
Create `tests/test_formatter.py`:
```python
from app.formatter import format_seconds_to_srt_time, format_seconds_to_vtt_time, segments_to_srt, segments_to_vtt, segments_to_txt

SAMPLE_SEGMENTS = [
    {"start": 0.0, "end": 2.5, "text": " Welcome to the lecture."},
    {"start": 2.5, "end": 6.123, "text": " Today we discuss machine learning."}
]

def test_srt_time_formatting():
    assert format_seconds_to_srt_time(0.0) == "00:00:00,000"
    assert format_seconds_to_srt_time(65.123) == "00:01:05,123"
    assert format_seconds_to_srt_time(3661.045) == "01:01:01,045"

def test_vtt_time_formatting():
    assert format_seconds_to_vtt_time(0.0) == "00:00:00.000"
    assert format_seconds_to_vtt_time(65.123) == "00:01:05.123"

def test_segments_to_srt():
    srt = segments_to_srt(SAMPLE_SEGMENTS)
    expected = (
        "1\n00:00:00,000 --> 00:00:02,500\nWelcome to the lecture.\n\n"
        "2\n00:00:02,500 --> 00:00:06,123\nToday we discuss machine learning.\n\n"
    )
    assert srt == expected

def test_segments_to_vtt():
    vtt = segments_to_vtt(SAMPLE_SEGMENTS)
    assert vtt.startswith("WEBVTT\n\n")
    assert "00:00:00.000 --> 00:00:02.500\nWelcome to the lecture." in vtt

def test_segments_to_txt():
    txt = segments_to_txt(SAMPLE_SEGMENTS)
    assert txt == "Welcome to the lecture. Today we discuss machine learning."
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_formatter.py`  
Expected: FAIL (ImportError: cannot import name 'format_seconds_to_srt_time')

**Step 3: Write minimal implementation**
Create `app/formatter.py`:
```python
from typing import Any

def format_seconds_to_srt_time(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    hours, rem = divmod(total_ms, 3600000)
    minutes, rem = divmod(rem, 60000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"

def format_seconds_to_vtt_time(seconds: float) -> str:
    srt_time = format_seconds_to_srt_time(seconds)
    return srt_time.replace(",", ".")

def segments_to_srt(segments: list[dict[str, Any]]) -> str:
    lines = []
    for idx, seg in enumerate(segments, 1):
        start = format_seconds_to_srt_time(float(seg["start"]))
        end = format_seconds_to_srt_time(float(seg["end"]))
        text = str(seg["text"]).strip()
        lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines) + ("\n" if lines else "")

def segments_to_vtt(segments: list[dict[str, Any]]) -> str:
    lines = ["WEBVTT\n"]
    for idx, seg in enumerate(segments, 1):
        start = format_seconds_to_vtt_time(float(seg["start"]))
        end = format_seconds_to_vtt_time(float(seg["end"]))
        text = str(seg["text"]).strip()
        lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)

def segments_to_txt(segments: list[dict[str, Any]]) -> str:
    chunks = [str(seg["text"]).strip() for seg in segments if str(seg["text"]).strip()]
    return " ".join(chunks)
```

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_formatter.py`  
Expected: PASS

**Step 5: Commit**
```bash
git add app/formatter.py tests/test_formatter.py
git commit -m "feat(formatter): add .txt, .srt, and .vtt transcript formatters"
```

---

### Task 3: FFmpeg Audio Extraction & Probing

**Files:**
- Create: `app/audio.py`
- Test: `tests/test_audio.py`

**Step 1: Write failing test**
Create `tests/test_audio.py`:
```python
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.audio import build_ffmpeg_extract_cmd, parse_duration_from_ffmpeg_output

def test_build_ffmpeg_extract_cmd():
    cmd = build_ffmpeg_extract_cmd(Path("video.mp4"), Path("audio.wav"))
    assert cmd[0] == "ffmpeg"
    assert "-i" in cmd
    assert "-vn" in cmd
    assert "-ar" in cmd
    assert "16000" in cmd
    assert "-ac" in cmd
    assert "1" in cmd

def test_parse_duration_from_ffmpeg_output():
    sample_stderr = """
    Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'sample.mp4':
      Duration: 01:23:45.67, start: 0.000000, bitrate: 1250 kb/s
    """
    duration = parse_duration_from_ffmpeg_output(sample_stderr)
    assert duration == (1 * 3600) + (23 * 60) + 45.67
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_audio.py`  
Expected: FAIL (ImportError: cannot import name 'build_ffmpeg_extract_cmd')

**Step 3: Write minimal implementation**
Create `app/audio.py`:
```python
import re
import shutil
import subprocess
from pathlib import Path

def find_ffmpeg_binary() -> str:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path
    # Check common Windows paths or imageio-ffmpeg fallback
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
    raise RuntimeError("FFmpeg is not installed or not found on PATH.")

def build_ffmpeg_extract_cmd(input_file: Path, output_file: Path, ffmpeg_bin: str = "ffmpeg") -> list[str]:
    return [
        ffmpeg_bin,
        "-y",
        "-i", str(input_file),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(output_file)
    ]

def parse_duration_from_ffmpeg_output(output: str) -> float | None:
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", output)
    if not match:
        return None
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)

def extract_audio(input_file: Path, output_file: Path) -> float:
    ffmpeg_bin = find_ffmpeg_binary()
    cmd = build_ffmpeg_extract_cmd(input_file, output_file, ffmpeg_bin=ffmpeg_bin)
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {process.stderr}")
    
    duration = parse_duration_from_ffmpeg_output(process.stderr)
    return duration or 0.0
```

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_audio.py`  
Expected: PASS

**Step 5: Commit**
```bash
git add app/audio.py tests/test_audio.py
git commit -m "feat(audio): add ffmpeg command builder and duration parser"
```

---

### Task 4: faster-whisper Model Wrapper & Generator

**Files:**
- Create: `app/transcription.py`
- Test: `tests/test_transcription.py`

**Step 1: Write failing test**
Create `tests/test_transcription.py`:
```python
from unittest.mock import MagicMock, patch
from pathlib import Path
from app.transcription import WhisperEngine

def test_whisper_engine_transcribe_generator():
    mock_model = MagicMock()
    mock_segment_1 = MagicMock(start=0.0, end=2.0, text="Hello world")
    mock_segment_2 = MagicMock(start=2.0, end=5.0, text="Test presentation")
    mock_info = MagicMock(language="en", duration=5.0)
    mock_model.transcribe.return_value = ([mock_segment_1, mock_segment_2], mock_info)

    engine = WhisperEngine(model_name="small", cpu_threads=4)
    engine._model = mock_model

    segments = []
    for seg, info in engine.transcribe(Path("fake_audio.wav")):
        segments.append(seg)

    assert len(segments) == 2
    assert segments[0]["text"] == "Hello world"
    assert segments[1]["end"] == 5.0
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_transcription.py`  
Expected: FAIL (ImportError: cannot import name 'WhisperEngine')

**Step 3: Write minimal implementation**
Create `app/transcription.py`:
```python
from pathlib import Path
from typing import Any, Generator
from faster_whisper import WhisperModel
from app.config import settings

class WhisperEngine:
    def __init__(self, model_name: str = "small", cpu_threads: int = 6):
        self.model_name = model_name
        self.cpu_threads = cpu_threads
        self._model: WhisperModel | None = None

    def load_model(self) -> WhisperModel:
        if self._model is None:
            self._model = WhisperModel(
                self.model_name,
                device="cpu",
                compute_type="int8",
                cpu_threads=self.cpu_threads,
                download_root=str(settings.MODELS_DIR)
            )
        return self._model

    def transcribe(
        self,
        audio_path: Path,
        language: str | None = None,
        initial_prompt: str | None = None
    ) -> Generator[tuple[dict[str, Any], Any], None, None]:
        model = self.load_model()
        segments_gen, info = model.transcribe(
            str(audio_path),
            language=language or None,
            initial_prompt=initial_prompt or None,
            beam_size=5,
            vad_filter=True
        )
        for segment in segments_gen:
            yield {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            }, info
```

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_transcription.py`  
Expected: PASS

**Step 5: Commit**
```bash
git add app/transcription.py tests/test_transcription.py
git commit -m "feat(transcription): add faster-whisper engine wrapper with streaming segments"
```

---

### Task 5: Job Manager & Background Task Orchestration

**Files:**
- Create: `app/job_manager.py`
- Test: `tests/test_job_manager.py`

**Step 1: Write failing test**
Create `tests/test_job_manager.py`:
```python
from pathlib import Path
from app.job_manager import JobManager, JobStatus

def test_job_lifecycle():
    jm = JobManager(base_dir=Path("data/test_jobs"))
    job_id = jm.create_job(filename="presentation.mp4", model_size="small")
    
    job = jm.get_job(job_id)
    assert job["status"] == JobStatus.QUEUED
    assert job["filename"] == "presentation.mp4"
    assert job["progress"] == 0.0

    jm.update_status(job_id, JobStatus.EXTRACTING)
    assert jm.get_job(job_id)["status"] == JobStatus.EXTRACTING

    jm.update_progress(job_id, progress=45.5, current_time=91.0, total_duration=200.0)
    job = jm.get_job(job_id)
    assert job["progress"] == 45.5
    assert job["current_time"] == 91.0

    jm.complete_job(job_id, segments=[{"start": 0.0, "end": 2.0, "text": "Testing"}])
    job = jm.get_job(job_id)
    assert job["status"] == JobStatus.COMPLETED
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_job_manager.py`  
Expected: FAIL (ImportError: cannot import name 'JobManager')

**Step 3: Write minimal implementation**
Create `app/job_manager.py`:
```python
import uuid
import time
from enum import Enum
from pathlib import Path
from typing import Any
from app.formatter import segments_to_txt, segments_to_srt, segments_to_vtt

class JobStatus(str, Enum):
    QUEUED = "queued"
    EXTRACTING = "extracting_audio"
    TRANSCRIBING = "transcribing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobManager:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.jobs: dict[str, dict[str, Any]] = {}

    def create_job(self, filename: str, model_size: str, initial_prompt: str | None = None) -> str:
        job_id = str(uuid.uuid4())
        job_dir = self.base_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        self.jobs[job_id] = {
            "job_id": job_id,
            "filename": filename,
            "model_size": model_size,
            "initial_prompt": initial_prompt,
            "status": JobStatus.QUEUED,
            "progress": 0.0,
            "current_time": 0.0,
            "total_duration": 0.0,
            "error": None,
            "job_dir": job_dir,
            "created_at": time.time(),
            "updated_at": time.time(),
            "segments": [],
            "files": {}
        }
        return job_id

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        return self.jobs.get(job_id)

    def update_status(self, job_id: str, status: JobStatus, error: str | None = None) -> None:
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = status
            self.jobs[job_id]["error"] = error
            self.jobs[job_id]["updated_at"] = time.time()

    def update_progress(self, job_id: str, progress: float, current_time: float, total_duration: float) -> None:
        if job_id in self.jobs:
            self.jobs[job_id]["progress"] = round(progress, 1)
            self.jobs[job_id]["current_time"] = round(current_time, 1)
            self.jobs[job_id]["total_duration"] = round(total_duration, 1)
            self.jobs[job_id]["updated_at"] = time.time()

    def complete_job(self, job_id: str, segments: list[dict[str, Any]]) -> None:
        if job_id not in self.jobs:
            return
        job = self.jobs[job_id]
        job_dir: Path = job["job_dir"]

        txt_content = segments_to_txt(segments)
        srt_content = segments_to_srt(segments)
        vtt_content = segments_to_vtt(segments)

        txt_path = job_dir / "transcript.txt"
        srt_path = job_dir / "subtitles.srt"
        vtt_path = job_dir / "subtitles.vtt"

        txt_path.write_text(txt_content, encoding="utf-8")
        srt_path.write_text(srt_content, encoding="utf-8")
        vtt_path.write_text(vtt_content, encoding="utf-8")

        job["segments"] = segments
        job["status"] = JobStatus.COMPLETED
        job["progress"] = 100.0
        job["files"] = {
            "txt": txt_path,
            "srt": srt_path,
            "vtt": vtt_path
        }
        job["preview"] = txt_content[:2000]
        job["updated_at"] = time.time()
```

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_job_manager.py`  
Expected: PASS

**Step 5: Commit**
```bash
git add app/job_manager.py tests/test_job_manager.py
git commit -m "feat(jobs): add JobManager with status tracking and file generation"
```

---

### Task 6: FastAPI Application & REST Endpoints

**Files:**
- Create: `app/main.py`
- Test: `tests/test_api.py`

**Step 1: Write failing test**
Create `tests/test_api.py`:
```python
import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_create_job_endpoint():
    dummy_file = io.BytesIO(b"dummy audio content")
    response = client.post(
        "/api/jobs",
        files={"file": ("test.wav", dummy_file, "audio/wav")},
        data={"model_size": "small", "initial_prompt": "AI lecture"}
    )
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_api.py`  
Expected: FAIL (ModuleNotFoundError: No module named 'app.main')

**Step 3: Write minimal implementation**
Create `app/main.py`:
```python
import shutil
import asyncio
from concurrent.futures import ThreadPoolExecutor
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
executor = ThreadPoolExecutor(max_workers=2)

def run_transcription_pipeline(job_id: str, source_path: Path, model_size: str, initial_prompt: str | None):
    job = job_manager.get_job(job_id)
    if not job:
        return
    job_dir = job["job_dir"]
    audio_path = job_dir / "extracted_audio.wav"

    try:
        job_manager.update_status(job_id, JobStatus.EXTRACTING)
        duration = extract_audio(source_path, audio_path)
        job_manager.update_progress(job_id, 0.0, 0.0, duration)

        # Remove raw video upload to save disk space
        if source_path.exists():
            source_path.unlink()

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
        raise HTTPException(status_code=400, detail=f"Unsupported model: {model_size}")

    job_id = job_manager.create_job(filename=file.filename or "upload.mp4", model_size=model_size, initial_prompt=initial_prompt)
    job_dir = job_manager.get_job(job_id)["job_dir"]
    source_path = job_dir / f"source_{file.filename}"

    # Stream file to disk in 1MB chunks
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
    return FileResponse(file_path, filename=f"{stem}.{fmt}", media_type="text/plain")

@app.get("/api/jobs/{job_id}/events")
async def job_events(job_id: str):
    async def event_generator():
        while True:
            job = job_manager.get_job(job_id)
            if not job:
                yield {"event": "error", "data": "Job not found"}
                break
            payload = {
                "status": job["status"],
                "progress": job["progress"],
                "current_time": job["current_time"],
                "total_duration": job["total_duration"],
                "error": job["error"]
            }
            yield {"event": "update", "data": payload}
            if job["status"] in [JobStatus.COMPLETED, JobStatus.FAILED]:
                break
            await asyncio.sleep(1.0)

    return EventSourceResponse(event_generator())

# Mount static web UI files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
```

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_api.py`  
Expected: PASS

**Step 5: Commit**
```bash
git add app/main.py tests/test_api.py
git commit -m "feat(api): add FastAPI job creation, status polling, and download routes"
```

---

### Task 7: Drag-and-Drop Web UI (HTML5, Tailwind, JS)

**Files:**
- Create: `app/static/index.html`
- Create: `app/static/app.js`
- Create: `app/static/style.css`

**Step 1: Write UI Structure**
Create `app/static/index.html`:
- Modern centered card layout with Tailwind CSS.
- Large Drag-and-Drop dropzone supporting video/audio file types.
- Model selector dropdown (`base`, `small` [default], `medium`).
- Academic vocabulary prompt textarea (hints for Whisper).
- Real-time animated progress bar showing current stage & timestamp.
- Results panel:
  - Copy for NotebookLM button (with visual copied feedback).
  - Download buttons for `.txt`, `.srt`, `.vtt`.
  - Scrollable transcript preview container.

**Step 2: Write Client JavaScript**
Create `app/static/app.js`:
- Drag-and-drop file listeners (`dragover`, `dragleave`, `drop`).
- Streaming `XMLHttpRequest` or `fetch` upload with upload progress.
- Server-Sent Events (SSE) `EventSource` connection to `/api/jobs/{job_id}/events`.
- Clipboard API integration for NotebookLM instant copy.
- Dynamic error alerts and reset button.

**Step 3: Verify in browser / Static test**
Verify static files serve correctly via FastAPI `TestClient`:
```python
def test_static_index_serves():
    response = client.get("/")
    assert response.status_code == 200
    assert "Video to Text" in response.text
```

**Step 4: Commit**
```bash
git add app/static/index.html app/static/app.js app/static/style.css
git commit -m "feat(ui): add modern drag-and-drop interface with live progress tracking"
```

---

### Task 8: Server CLI Runner & End-to-End Verification

**Files:**
- Create: `run.py`
- Create: `tests/test_e2e.py`

**Step 1: Write CLI entrypoint**
Create `run.py`:
```python
import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"Starting {settings.APP_NAME} at http://{settings.HOST}:{settings.PORT}")
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
```

**Step 2: Write End-to-End Synthetic Audio Test**
Create `tests/test_e2e.py` which:
- Generates a synthetic 2-second WAV file using standard Python `wave` module.
- Posts to `/api/jobs`.
- Verifies successful extraction, processing, and output of `.txt` and `.srt`.

**Step 3: Run Full Pytest Suite**
Run: `pytest -v`  
Expected: All tests pass.

**Step 4: Commit**
```bash
git add run.py tests/test_e2e.py
git commit -m "feat: add CLI runner and end-to-end synthetic verification test"
```
