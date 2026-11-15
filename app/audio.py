import re
import shutil
import subprocess
from pathlib import Path

def find_ffmpeg_binary() -> str:
    # 1. Check system PATH
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path

    # 2. Check current Python environment via imageio_ffmpeg
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError):
        pass

    # 3. Check local .venv binaries directory (fallback if run from global python)
    root_dir = Path(__file__).resolve().parent.parent
    venv_binaries = root_dir / ".venv" / "Lib" / "site-packages" / "imageio_ffmpeg" / "binaries"
    if venv_binaries.exists():
        for exe in venv_binaries.glob("ffmpeg*.exe"):
            return str(exe)

    raise RuntimeError(
        "FFmpeg is not installed or not found on PATH. "
        "Please run with the virtual environment: '.venv\\Scripts\\python run.py' or run '.\\start.bat'."
    )

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
    process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {process.stderr}")
    
    duration = parse_duration_from_ffmpeg_output(process.stderr)
    return duration or 0.0
