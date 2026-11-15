import io
import math
import struct
import wave
import time
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app, job_manager

client = TestClient(app)

def create_synthetic_wav() -> bytes:
    """Generates a 1-second 440Hz sine wave WAV file in memory."""
    buf = io.BytesIO()
    sample_rate = 16000
    duration = 1.0
    frequency = 440.0
    num_samples = int(sample_rate * duration)

    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        frames = bytearray()
        for i in range(num_samples):
            value = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * frequency * (i / sample_rate)))
            frames.extend(struct.pack("<h", value))
        wav_file.writeframes(frames)

    return buf.getvalue()

def test_end_to_end_pipeline():
    audio_bytes = create_synthetic_wav()

    # 1. Post job to /api/jobs
    response = client.post(
        "/api/jobs",
        files={"file": ("synthetic_sample.wav", io.BytesIO(audio_bytes), "audio/wav")},
        data={"model_size": "base"}
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    assert job_id is not None

    # 2. Poll until pipeline finishes
    max_wait_seconds = 60
    start_time = time.time()
    final_status = None

    while time.time() - start_time < max_wait_seconds:
        status_resp = client.get(f"/api/jobs/{job_id}")
        assert status_resp.status_code == 200
        data = status_resp.json()
        final_status = data["status"]
        if final_status in ["completed", "failed"]:
            break
        time.sleep(0.5)

    assert final_status == "completed", f"Job failed: {data.get('error')}"
    assert data["progress"] == 100.0

    # 3. Check downloads
    resp_txt = client.get(f"/api/jobs/{job_id}/download/txt")
    assert resp_txt.status_code == 200
    assert "attachment" in resp_txt.headers["content-disposition"]

    resp_srt = client.get(f"/api/jobs/{job_id}/download/srt")
    assert resp_srt.status_code == 200

    resp_vtt = client.get(f"/api/jobs/{job_id}/download/vtt")
    assert resp_vtt.status_code == 200
    assert "WEBVTT" in resp_vtt.text
