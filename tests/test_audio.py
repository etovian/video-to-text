from pathlib import Path
from unittest.mock import patch, MagicMock
from app.audio import (
    find_ffmpeg_binary,
    build_ffmpeg_extract_cmd,
    parse_duration_from_ffmpeg_output,
    extract_audio
)

def test_find_ffmpeg_binary():
    bin_path = find_ffmpeg_binary()
    assert bin_path is not None
    assert "ffmpeg" in bin_path.lower()

def test_build_ffmpeg_extract_cmd():
    cmd = build_ffmpeg_extract_cmd(Path("video.mp4"), Path("audio.wav"), ffmpeg_bin="ffmpeg")
    assert cmd[0] == "ffmpeg"
    assert "-y" in cmd
    assert "-i" in cmd
    assert str(Path("video.mp4")) in cmd
    assert "-vn" in cmd
    assert "-acodec" in cmd
    assert "pcm_s16le" in cmd
    assert "-ar" in cmd
    assert "16000" in cmd
    assert "-ac" in cmd
    assert "1" in cmd
    assert str(Path("audio.wav")) in cmd

def test_parse_duration_from_ffmpeg_output():
    sample_stderr = """
    Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'sample.mp4':
      Duration: 01:23:45.67, start: 0.000000, bitrate: 1250 kb/s
    """
    duration = parse_duration_from_ffmpeg_output(sample_stderr)
    assert duration == (1 * 3600) + (23 * 60) + 45.67

def test_parse_duration_missing():
    assert parse_duration_from_ffmpeg_output("No duration here") is None

@patch("subprocess.run")
def test_extract_audio_success(mock_subproc):
    mock_subproc.return_value = MagicMock(
        returncode=0,
        stderr="Duration: 00:02:30.00, start: 0.000000"
    )
    duration = extract_audio(Path("input.mp4"), Path("output.wav"))
    assert duration == 150.0

@patch("subprocess.run")
def test_extract_audio_failure(mock_subproc):
    mock_subproc.return_value = MagicMock(
        returncode=1,
        stderr="Invalid data found when processing input"
    )
    import pytest
    with pytest.raises(RuntimeError, match="FFmpeg audio extraction failed"):
        extract_audio(Path("bad.mp4"), Path("output.wav"))
