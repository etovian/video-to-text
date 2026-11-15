// State
let selectedFile = null;
let currentJobId = null;
let eventSource = null;
let startTime = null;
let timerInterval = null;

// DOM Elements
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const fileInfo = document.getElementById("file-info");
const modelSelect = document.getElementById("model-select");
const promptInput = document.getElementById("prompt-input");
const startBtn = document.getElementById("start-btn");

const uploadCard = document.getElementById("upload-card");
const progressCard = document.getElementById("progress-card");
const progressStatusText = document.getElementById("progress-status-text");
const progressDetailText = document.getElementById("progress-detail-text");
const progressPct = document.getElementById("progress-pct");
const progressBarFill = document.getElementById("progress-bar-fill");
const progressTime = document.getElementById("progress-time");
const progressElapsed = document.getElementById("progress-elapsed");

const errorCard = document.getElementById("error-card");
const errorMessage = document.getElementById("error-message");
const errorResetBtn = document.getElementById("error-reset-btn");

const resultsCard = document.getElementById("results-card");
const resultFilename = document.getElementById("result-filename");
const transcriptPreview = document.getElementById("transcript-preview");
const copyBtn = document.getElementById("copy-btn");
const copyIcon = document.getElementById("copy-icon");
const copyText = document.getElementById("copy-text");
const dlTxtBtn = document.getElementById("dl-txt-btn");
const dlSrtBtn = document.getElementById("dl-srt-btn");
const dlVttBtn = document.getElementById("dl-vtt-btn");
const newTranscriptionBtn = document.getElementById("new-transcription-btn");

// Format helpers
function formatBytes(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

function formatDuration(seconds) {
    if (!seconds || isNaN(seconds)) return "00:00:00";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

// Drag and drop listeners
dropZone.addEventListener("click", () => fileInput.click());

dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("border-indigo-400", "bg-slate-800");
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("border-indigo-400", "bg-slate-800");
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("border-indigo-400", "bg-slate-800");
    if (e.dataTransfer.files.length > 0) {
        handleFileSelect(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
        handleFileSelect(fileInput.files[0]);
    }
});

function handleFileSelect(file) {
    selectedFile = file;
    fileInfo.textContent = `${file.name} (${formatBytes(file.size)})`;
    fileInfo.classList.remove("hidden");
    startBtn.disabled = false;
}

// Timer
function startTimer() {
    startTime = Date.now();
    timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const m = Math.floor(elapsed / 60);
        const s = elapsed % 60;
        progressElapsed.textContent = `Elapsed: ${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    }, 1000);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

// Start Transcription Flow
startBtn.addEventListener("click", () => {
    if (!selectedFile) return;

    // Reset views
    errorCard.classList.add("hidden");
    resultsCard.classList.add("hidden");
    progressCard.classList.remove("hidden");
    uploadCard.classList.add("opacity-50", "pointer-events-none");

    progressStatusText.textContent = "Uploading file...";
    progressDetailText.textContent = `Streaming ${formatBytes(selectedFile.size)} to local service...`;
    progressPct.textContent = "0%";
    progressBarFill.style.width = "0%";
    progressTime.textContent = "Uploading...";
    startTimer();

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("model_size", modelSelect.value);
    if (promptInput.value.trim()) {
        formData.append("initial_prompt", promptInput.value.trim());
    }

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/jobs", true);

    xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
            const pct = Math.round((e.loaded / e.total) * 100);
            progressBarFill.style.width = `${pct}%`;
            progressPct.textContent = `${pct}%`;
            if (pct === 100) {
                progressStatusText.textContent = "Processing upload...";
                progressDetailText.textContent = "File stored, preparing transcription pipeline...";
            }
        }
    };

    xhr.onload = () => {
        if (xhr.status === 202) {
            const data = JSON.parse(xhr.responseText);
            currentJobId = data.job_id;
            listenForJobEvents(currentJobId);
        } else {
            handleError(`Upload failed with status ${xhr.status}: ${xhr.statusText}`);
        }
    };

    xhr.onerror = () => {
        handleError("Network or server connection error during upload.");
    };

    xhr.send(formData);
});

// SSE Stream for real-time progress
function listenForJobEvents(jobId) {
    if (eventSource) {
        eventSource.close();
    }

    progressBarFill.style.width = "0%";
    progressPct.textContent = "0%";

    eventSource = new EventSource(`/api/jobs/${jobId}/events`);

    eventSource.addEventListener("update", (e) => {
        const data = JSON.parse(e.data);
        const status = data.status;
        const progress = data.progress || 0;

        progressBarFill.style.width = `${progress}%`;
        progressPct.textContent = `${Math.round(progress)}%`;

        if (status === "extracting_audio") {
            progressStatusText.textContent = "Extracting Audio (FFmpeg)...";
            progressDetailText.textContent = "Stripping video frames to generate clean 16 kHz mono track...";
            progressTime.textContent = "Audio preparation";
        } else if (status === "transcribing") {
            progressStatusText.textContent = "Transcribing with Whisper...";
            progressDetailText.textContent = `Running CPU INT8 inference (${modelSelect.value} model)`;
            progressTime.textContent = `${formatDuration(data.current_time)} / ${formatDuration(data.total_duration)}`;
        } else if (status === "completed") {
            eventSource.close();
            stopTimer();
            displayResults(jobId);
        } else if (status === "failed") {
            eventSource.close();
            stopTimer();
            handleError(data.error || "An unknown transcription error occurred.");
        }
    });

    eventSource.addEventListener("error", () => {
        // Fallback polling if SSE disconnects
        eventSource.close();
        pollJobStatus(jobId);
    });
}

// Fallback Polling
async function pollJobStatus(jobId) {
    try {
        const resp = await fetch(`/api/jobs/${jobId}`);
        if (!resp.ok) return;
        const data = await resp.json();

        if (data.status === "completed") {
            stopTimer();
            displayResults(jobId);
        } else if (data.status === "failed") {
            stopTimer();
            handleError(data.error);
        } else {
            progressBarFill.style.width = `${data.progress}%`;
            progressPct.textContent = `${Math.round(data.progress)}%`;
            progressTime.textContent = `${formatDuration(data.current_time)} / ${formatDuration(data.total_duration)}`;
            setTimeout(() => pollJobStatus(jobId), 1500);
        }
    } catch (e) {
        setTimeout(() => pollJobStatus(jobId), 2000);
    }
}

// Display Completed Results
async function displayResults(jobId) {
    progressCard.classList.add("hidden");
    resultsCard.classList.remove("hidden");

    resultFilename.textContent = selectedFile ? selectedFile.name : "Transcript Ready";
    dlTxtBtn.href = `/api/jobs/${jobId}/download/txt`;
    dlSrtBtn.href = `/api/jobs/${jobId}/download/srt`;
    dlVttBtn.href = `/api/jobs/${jobId}/download/vtt`;

    // Fetch the transcript text for the preview
    try {
        const resp = await fetch(`/api/jobs/${jobId}/download/txt`);
        const text = await resp.text();
        transcriptPreview.textContent = text || "(No text transcribed)";
    } catch (e) {
        transcriptPreview.textContent = "Could not load preview text.";
    }
}

// One-click Copy for Google NotebookLM
copyBtn.addEventListener("click", async () => {
    const textToCopy = transcriptPreview.textContent;
    if (!textToCopy) return;

    try {
        await navigator.clipboard.writeText(textToCopy);
        copyIcon.textContent = "✓";
        copyText.textContent = "Copied to Clipboard!";
        copyBtn.classList.replace("bg-emerald-600", "bg-emerald-700");

        setTimeout(() => {
            copyIcon.textContent = "📋";
            copyText.textContent = "Copy for NotebookLM";
            copyBtn.classList.replace("bg-emerald-700", "bg-emerald-600");
        }, 2500);
    } catch (err) {
        alert("Failed to copy to clipboard.");
    }
});

// Reset for another file
function resetUI() {
    stopTimer();
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }
    selectedFile = null;
    fileInput.value = "";
    fileInfo.classList.add("hidden");
    startBtn.disabled = true;

    uploadCard.classList.remove("opacity-50", "pointer-events-none");
    progressCard.classList.add("hidden");
    errorCard.classList.add("hidden");
    resultsCard.classList.add("hidden");
}

newTranscriptionBtn.addEventListener("click", resetUI);
errorResetBtn.addEventListener("click", resetUI);

function handleError(errText) {
    progressCard.classList.add("hidden");
    errorCard.classList.remove("hidden");
    errorMessage.textContent = errText;
}
