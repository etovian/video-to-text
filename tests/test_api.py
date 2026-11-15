import io
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import pytest
from app.main import app, job_manager
from app.job_manager import JobStatus

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Video-to-Text" in data["app"]

def test_create_job_invalid_model():
    dummy_file = io.BytesIO(b"dummy audio content")
    response = client.post(
        "/api/jobs",
        files={"file": ("test.wav", dummy_file, "audio/wav")},
        data={"model_size": "gigantic_model"}
    )
    assert response.status_code == 400
    assert "Unsupported model" in response.json()["detail"]

@patch("app.main.run_transcription_pipeline")
def test_create_job_success(mock_pipeline):
    dummy_file = io.BytesIO(b"fake audio data")
    response = client.post(
        "/api/jobs",
        files={"file": ("sample_lecture.mp4", dummy_file, "video/mp4")},
        data={"model_size": "small", "initial_prompt": "Physics Lecture"}
    )
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"

    job = job_manager.get_job(data["job_id"])
    assert job is not None
    assert job["filename"] == "sample_lecture.mp4"
    assert job["model_size"] == "small"

def test_get_job_status_not_found():
    response = client.get("/api/jobs/nonexistent-id")
    assert response.status_code == 404

def test_get_job_status_existing():
    job_id = job_manager.create_job(filename="talk.mp4", model_size="small")
    job_manager.update_progress(job_id, progress=42.0, current_time=84.0, total_duration=200.0)

    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert data["progress"] == 42.0
    assert data["total_duration"] == 200.0

def test_download_transcript_flow():
    job_id = job_manager.create_job(filename="presentation.mp4", model_size="small")
    
    # Attempting to download before completion returns 404
    resp_early = client.get(f"/api/jobs/{job_id}/download/txt")
    assert resp_early.status_code == 404

    # Complete the job
    sample_segments = [
        {"start": 0.0, "end": 2.0, "text": " Good morning."},
        {"start": 2.0, "end": 4.5, "text": " Welcome to our presentation."}
    ]
    job_manager.complete_job(job_id, sample_segments)

    # Download txt
    resp_txt = client.get(f"/api/jobs/{job_id}/download/txt")
    assert resp_txt.status_code == 200
    assert "Good morning. Welcome to our presentation." in resp_txt.text
    assert resp_txt.headers["content-disposition"].startswith('attachment; filename="presentation.txt"')

    # Download srt
    resp_srt = client.get(f"/api/jobs/{job_id}/download/srt")
    assert resp_srt.status_code == 200
    assert "00:00:00,000 --> 00:00:02,000" in resp_srt.text

    # Download vtt
    resp_vtt = client.get(f"/api/jobs/{job_id}/download/vtt")
    assert resp_vtt.status_code == 200
    assert "WEBVTT" in resp_vtt.text

    # Invalid format returns 400
    resp_bad = client.get(f"/api/jobs/{job_id}/download/pdf")
    assert resp_bad.status_code == 400
