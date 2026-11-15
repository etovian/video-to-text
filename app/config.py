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
