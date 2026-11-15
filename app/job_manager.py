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
            "files": {},
            "preview": None
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
