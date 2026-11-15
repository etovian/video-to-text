from pathlib import Path
from typing import Any, Generator
from faster_whisper import WhisperModel
from app.config import settings

class WhisperEngine:
    def __init__(self, model_name: str = "small", cpu_threads: int = 6):
        self.model_name = model_name
        self.cpu_threads = cpu_threads
        self._model: WhisperModel | None = None

    def load_model(self) -> WhisperModel:
        if self._model is None:
            self._model = WhisperModel(
                self.model_name,
                device="cpu",
                compute_type="int8",
                cpu_threads=self.cpu_threads,
                download_root=str(settings.MODELS_DIR)
            )
        return self._model

    def transcribe(
        self,
        audio_path: Path,
        language: str | None = None,
        initial_prompt: str | None = None
    ) -> Generator[tuple[dict[str, Any], Any], None, None]:
        model = self.load_model()
        segments_gen, info = model.transcribe(
            str(audio_path),
            language=language or None,
            initial_prompt=initial_prompt or None,
            beam_size=5,
            vad_filter=True
        )
        for segment in segments_gen:
            yield {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            }, info
