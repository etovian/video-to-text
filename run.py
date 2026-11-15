import sys
import subprocess
from pathlib import Path

# Auto-switch to virtual environment if run from global Python
root_dir = Path(__file__).resolve().parent
venv_python = root_dir / ".venv" / "Scripts" / "python.exe"

if venv_python.exists():
    try:
        current_exe = Path(sys.executable).resolve()
        target_exe = venv_python.resolve()
        if current_exe != target_exe:
            # Re-launch using the virtual environment interpreter
            ret = subprocess.call([str(venv_python)] + sys.argv)
            sys.exit(ret)
    except Exception:
        pass

import uvicorn
from app.config import settings
from app.audio import find_ffmpeg_binary

def main():
    print("=" * 60)
    print(f"  {settings.APP_NAME}")
    print("=" * 60)
    
    # Ensure working directories
    settings.ensure_directories()
    
    # Check FFmpeg
    try:
        ffmpeg_exe = find_ffmpeg_binary()
        print(f"✓ FFmpeg found: {ffmpeg_exe}")
    except RuntimeError as e:
        print(f"❌ FFmpeg check failed: {e}")
        sys.exit(1)

    print(f"✓ Python Environment: {sys.executable}")
    print(f"✓ CPU Threads allocated: {settings.CPU_THREADS}")
    print(f"✓ Supported Models: {', '.join(settings.SUPPORTED_MODELS)}")
    print(f"✓ Default Model: {settings.DEFAULT_MODEL}")
    print(f"\n🚀 Web Interface running at: http://{settings.HOST}:{settings.PORT}")
    print("   Open this URL in your browser to start transcribing.")
    print("=" * 60 + "\n")

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level="info"
    )

if __name__ == "__main__":
    main()
