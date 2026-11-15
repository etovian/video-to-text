from app.formatter import (
    format_seconds_to_srt_time,
    format_seconds_to_vtt_time,
    segments_to_srt,
    segments_to_vtt,
    segments_to_txt
)

SAMPLE_SEGMENTS = [
    {"start": 0.0, "end": 2.5, "text": " Welcome to the lecture."},
    {"start": 2.5, "end": 6.123, "text": " Today we discuss machine learning."}
]

def test_srt_time_formatting():
    assert format_seconds_to_srt_time(0.0) == "00:00:00,000"
    assert format_seconds_to_srt_time(65.123) == "00:01:05,123"
    assert format_seconds_to_srt_time(3661.045) == "01:01:01,045"

def test_vtt_time_formatting():
    assert format_seconds_to_vtt_time(0.0) == "00:00:00.000"
    assert format_seconds_to_vtt_time(65.123) == "00:01:05.123"
    assert format_seconds_to_vtt_time(3661.045) == "01:01:01.045"

def test_segments_to_srt():
    srt = segments_to_srt(SAMPLE_SEGMENTS)
    expected = (
        "1\n00:00:00,000 --> 00:00:02,500\nWelcome to the lecture.\n\n"
        "2\n00:00:02,500 --> 00:00:06,123\nToday we discuss machine learning.\n\n"
    )
    assert srt == expected

def test_segments_to_vtt():
    vtt = segments_to_vtt(SAMPLE_SEGMENTS)
    assert vtt.startswith("WEBVTT\n\n")
    assert "00:00:00.000 --> 00:00:02.500\nWelcome to the lecture." in vtt
    assert "00:00:02.500 --> 00:00:06.123\nToday we discuss machine learning." in vtt

def test_segments_to_txt():
    txt = segments_to_txt(SAMPLE_SEGMENTS)
    assert txt == "Welcome to the lecture. Today we discuss machine learning."

def test_empty_segments():
    assert segments_to_srt([]) == ""
    assert segments_to_vtt([]) == "WEBVTT\n"
    assert segments_to_txt([]) == ""
