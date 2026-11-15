import shutil
from pathlib import Path
import pytest
from app.job_manager import JobManager, JobStatus

@pytest.fixture
def temp_jobs_dir(tmp_path):
    jobs_dir = tmp_path / "test_jobs"
    jobs_dir.mkdir()
    yield jobs_dir
    shutil.rmtree(jobs_dir, ignore_errors=True)

def test_job_creation(temp_jobs_dir):
    jm = JobManager(base_dir=temp_jobs_dir)
    job_id = jm.create_job(filename="lecture.mp4", model_size="small", initial_prompt="Physics 101")
    
    assert job_id is not None
    job = jm.get_job(job_id)
    assert job is not None
    assert job["filename"] == "lecture.mp4"
    assert job["model_size"] == "small"
    assert job["initial_prompt"] == "Physics 101"
    assert job["status"] == JobStatus.QUEUED
    assert job["progress"] == 0.0
    assert job["job_dir"].exists()

def test_job_status_and_progress_updates(temp_jobs_dir):
    jm = JobManager(base_dir=temp_jobs_dir)
    job_id = jm.create_job(filename="lecture.mp4", model_size="small")

    jm.update_status(job_id, JobStatus.EXTRACTING)
    assert jm.get_job(job_id)["status"] == JobStatus.EXTRACTING

    jm.update_progress(job_id, progress=50.25, current_time=150.75, total_duration=300.0)
    job = jm.get_job(job_id)
    assert job["progress"] == 50.2
    assert job["current_time"] == 150.8
    assert job["total_duration"] == 300.0

def test_job_completion_generates_files(temp_jobs_dir):
    jm = JobManager(base_dir=temp_jobs_dir)
    job_id = jm.create_job(filename="lecture.mp4", model_size="small")

    sample_segments = [
        {"start": 0.0, "end": 2.5, "text": " Welcome to the session."},
        {"start": 2.5, "end": 5.0, "text": " Let's begin."}
    ]
    jm.complete_job(job_id, sample_segments)

    job = jm.get_job(job_id)
    assert job["status"] == JobStatus.COMPLETED
    assert job["progress"] == 100.0
    assert "txt" in job["files"]
    assert "srt" in job["files"]
    assert "vtt" in job["files"]

    txt_file: Path = job["files"]["txt"]
    srt_file: Path = job["files"]["srt"]
    vtt_file: Path = job["files"]["vtt"]

    assert txt_file.exists()
    assert srt_file.exists()
    assert vtt_file.exists()

    assert "Welcome to the session. Let's begin." == txt_file.read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:02,500" in srt_file.read_text(encoding="utf-8")
    assert "WEBVTT" in vtt_file.read_text(encoding="utf-8")
    assert job["preview"] == "Welcome to the session. Let's begin."

def test_job_failure(temp_jobs_dir):
    jm = JobManager(base_dir=temp_jobs_dir)
    job_id = jm.create_job(filename="lecture.mp4", model_size="small")

    jm.update_status(job_id, JobStatus.FAILED, error="FFmpeg failed to extract audio")
    job = jm.get_job(job_id)
    assert job["status"] == JobStatus.FAILED
    assert job["error"] == "FFmpeg failed to extract audio"
