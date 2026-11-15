# Video to Text Transcriber 🎙️

A local, private REST API microservice and embedded web frontend designed to extract audio from large video and audio files (including 3.7+ GB academic presentations) and generate text transcripts optimized for [Google NotebookLM](https://notebook.google.com), alongside SubRip (`.srt`) and WebVTT (`.vtt`) subtitles.

Runs **100% locally and offline** using `faster-whisper` CPU INT8 quantization. Zero cloud API keys or GPU required.

---

## Features

- **Large File Streaming**: Streams multi-gigabyte video uploads directly to disk in chunks to keep memory usage under 100 MB.
- **Automated Audio Stripping**: FFmpeg automatically isolates a lightweight 16 kHz mono audio track and immediately prunes the large raw video file to save disk space.
- **Fast CPU Inference**: Powered by `faster-whisper` with 8-bit quantization (`int8`) and multi-threading optimized for modern multi-core CPUs.
- **NotebookLM Integration**: Dedicated one-click **"Copy for NotebookLM"** button and clean `.txt` export matching Google NotebookLM's input format.
- **Subtitle Export**: Generate standard `.srt` and `.vtt` subtitles with precise timestamps.
- **Real-Time Progress**: Live Server-Sent Events (SSE) progress bar displaying transcription stage, percentage, and audio timestamps.
- **Academic Jargon Guidance**: Optional prompt input to steer Whisper's spelling of domain-specific terminology, acronyms, and names.

---

## Quick Start

### 1. Requirements
- Python 3.11+
- Windows, macOS, or Linux

### 2. Setup
Create a virtual environment and install the dependencies:

```bash
python -m venv .venv
# On Windows:
.venv\Scripts\pip install -r requirements.txt
# On Linux/macOS:
.venv/bin/pip install -r requirements.txt
```

*(Note: FFmpeg is automatically bundled via `imageio-ffmpeg`—no manual installation needed!)*

### 3. Run the Application

```bash
# On Windows:
.venv\Scripts\python run.py
# On Linux/macOS:
.venv/bin/python run.py
```

Open your browser to:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## Running the Tests

To run the complete test suite (29 unit, integration, UI, and end-to-end tests):

```bash
.venv\Scripts\pytest -v
```

---

## Architecture Overview

```
video-to-text/
├── app/
│   ├── config.py             # Settings, directories, thread limits, supported models
│   ├── audio.py              # FFmpeg audio stripping and duration probing
│   ├── formatter.py          # .txt, .srt, .vtt subtitle formatters
│   ├── transcription.py      # faster-whisper wrapper with streaming segments
│   ├── job_manager.py        # Lifecycle state machine & scratch file management
│   ├── main.py               # FastAPI REST endpoints, SSE stream, and static UI mount
│   └── static/
│       ├── index.html        # Drag-and-drop web UI with Tailwind CSS
│       ├── app.js            # Upload streaming, SSE event listeners, clipboard copy
│       └── style.css         # Custom styling
├── tests/                    # 29 test cases covering all modules and E2E pipeline
├── docs/plans/               # Architecture design & implementation plan
├── requirements.txt
└── run.py                    # Server CLI entrypoint
```
