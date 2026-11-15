from typing import Any

def format_seconds_to_srt_time(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    hours, rem = divmod(total_ms, 3600000)
    minutes, rem = divmod(rem, 60000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"

def format_seconds_to_vtt_time(seconds: float) -> str:
    srt_time = format_seconds_to_srt_time(seconds)
    return srt_time.replace(",", ".")

def segments_to_srt(segments: list[dict[str, Any]]) -> str:
    if not segments:
        return ""
    lines = []
    for idx, seg in enumerate(segments, 1):
        start = format_seconds_to_srt_time(float(seg["start"]))
        end = format_seconds_to_srt_time(float(seg["end"]))
        text = str(seg.get("text", "")).strip()
        lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines) + "\n"

def segments_to_vtt(segments: list[dict[str, Any]]) -> str:
    lines = ["WEBVTT\n"]
    if not segments:
        return "\n".join(lines)
    for idx, seg in enumerate(segments, 1):
        start = format_seconds_to_vtt_time(float(seg["start"]))
        end = format_seconds_to_vtt_time(float(seg["end"]))
        text = str(seg.get("text", "")).strip()
        lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)

def segments_to_txt(segments: list[dict[str, Any]]) -> str:
    chunks = [str(seg.get("text", "")).strip() for seg in segments if str(seg.get("text", "")).strip()]
    return " ".join(chunks)
