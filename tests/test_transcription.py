from pathlib import Path
from unittest.mock import MagicMock, patch
from app.transcription import WhisperEngine

def test_whisper_engine_init():
    engine = WhisperEngine(model_name="small", cpu_threads=4)
    assert engine.model_name == "small"
    assert engine.cpu_threads == 4
    assert engine._model is None

@patch("app.transcription.WhisperModel")
def test_whisper_engine_load_model(mock_model_cls):
    mock_instance = MagicMock()
    mock_model_cls.return_value = mock_instance

    engine = WhisperEngine(model_name="base", cpu_threads=6)
    loaded = engine.load_model()

    assert loaded == mock_instance
    mock_model_cls.assert_called_once()
    args, kwargs = mock_model_cls.call_args
    assert args[0] == "base"
    assert kwargs["device"] == "cpu"
    assert kwargs["compute_type"] == "int8"
    assert kwargs["cpu_threads"] == 6

def test_whisper_engine_transcribe_generator():
    mock_model = MagicMock()
    mock_segment_1 = MagicMock(start=0.0, end=2.5, text=" Welcome to the lecture.")
    mock_segment_2 = MagicMock(start=2.5, end=6.123, text=" Machine learning overview.")
    mock_info = MagicMock(language="en", duration=6.123)
    mock_model.transcribe.return_value = ([mock_segment_1, mock_segment_2], mock_info)

    engine = WhisperEngine(model_name="small", cpu_threads=4)
    engine._model = mock_model

    segments = []
    info_out = None
    for seg, info in engine.transcribe(Path("fake_audio.wav"), initial_prompt="AI topic"):
        segments.append(seg)
        info_out = info

    assert len(segments) == 2
    assert segments[0]["start"] == 0.0
    assert segments[0]["end"] == 2.5
    assert segments[0]["text"] == " Welcome to the lecture."
    assert segments[1]["end"] == 6.123
    assert info_out.language == "en"

    mock_model.transcribe.assert_called_once_with(
        str(Path("fake_audio.wav")),
        language=None,
        initial_prompt="AI topic",
        beam_size=5,
        vad_filter=True
    )
