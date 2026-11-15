from pathlib import Path
from app.config import Settings

def test_default_settings():
    settings = Settings()
    assert settings.CPU_THREADS >= 1
    assert "small" in settings.SUPPORTED_MODELS
    assert settings.DEFAULT_MODEL == "small"
    assert isinstance(settings.DATA_DIR, Path)
    assert isinstance(settings.UPLOAD_DIR, Path)
    assert isinstance(settings.JOBS_DIR, Path)
