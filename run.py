import sys
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
