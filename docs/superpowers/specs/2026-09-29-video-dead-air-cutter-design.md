# Specification: Video Dead Air Cutter Desktop Application

- **Date:** 2026-09-29
- **Status:** Approved
- **Target OS:** Windows 10/11
- **Platform:** Python 3.10+ / PySide6

---

## 1. Objective

A desktop GUI application that takes a video file (MP4), detects dead air / silence segments using AI voice activity detection (Silero VAD), visualizes the detected active speech vs silence on an interactive timeline with video preview, and exports a trimmed MP4 with dead air removed.

---

## 2. Technology Stack

- **GUI Framework:** PySide6 (Qt6)
  - `QMediaPlayer` + `QVideoWidget` / `QAudioOutput` for video playback and preview.
  - Custom `QWidget` (`TimelineWidget`) using `QPainter` for rendering timeline intervals (speech vs dead air).
- **Voice Activity Detection:** `silero-vad` (ONNX runtime backend, CPU-friendly, lightweight).
- **Media Engine:** FFmpeg CLI (invoked via `subprocess` for extraction, slicing, and concatenation).

---

## 3. System Architecture & Modules

```text
video-air-gap-cut/
├── core/
│   ├── audio_extractor.py   # Extract 16kHz mono PCM WAV from input video via ffmpeg
│   ├── vad_detector.py      # Analyze WAV using Silero VAD (ONNX) to output speech timestamps
│   ├── timeline_planner.py  # Merge intervals, apply start/end padding, generate cut lists
│   └── video_processor.py   # Slice and concat video using ffmpeg filter_complex or concat demuxer
├── ui/
│   ├── main_window.py       # Main application window, orchestration, async worker threads
│   ├── video_player.py      # Video playback controls (play, pause, seek, time display)
│   └── timeline_widget.py   # Visual timeline showing green (speech) and red (cut) segments
├── main.py                  # Application entry point
└── requirements.txt         # Project dependencies
```

---

## 4. Key Workflows & Data Flow

### 4.1 Analysis Flow (Non-blocking via `QThread`)
1. User loads an MP4 file via File Picker or drag-and-drop.
2. `VideoPlayer` loads the video and displays initial frame and duration.
3. Background worker invokes `audio_extractor.py` to extract audio to a temporary 16kHz mono WAV file.
4. Background worker invokes `vad_detector.py` using Silero VAD ONNX model to produce a list of speech intervals: `[{ "start": float, "end": float }]` (in seconds).
5. `timeline_planner.py` applies user-configured parameters:
   - `speech_pad_ms` (default: 150ms): padding before and after speech to avoid cutting plosives/tails.
   - `min_silence_duration_ms` (default: 500ms): silence duration threshold below which dead air is not cut.
   - `threshold` (default: 0.5): VAD probability threshold.
6. Worker emits signal with calculated speech segments; UI updates `TimelineWidget`.

### 4.2 Playback & Preview
- `TimelineWidget` maps video duration across horizontal width.
  - **Green blocks**: retained speech segments.
  - **Red / Gray blocks**: dead air intervals to be trimmed.
- User can scrub/click the timeline to seek `QMediaPlayer` to any timestamp.

### 4.3 Export & Cut Flow
1. User clicks "Export Trimmed Video" and selects output MP4 path.
2. `video_processor.py` constructs an FFmpeg command:
   - Uses `concat` filter (or re-encode with high-speed preset `libx264` + `aac`) to ensure exact frame cuts without desync.
3. Progress is monitored and reported back to UI progress bar.
4. Temporary audio files are cleaned up upon completion.

---

## 5. Error Handling & Edge Cases

- **No speech detected:** Notify user via dialog; do not cut entire video.
- **No silence detected:** Notify user that no dead air was found.
- **FFmpeg missing:** Check for `ffmpeg` availability on startup; show clear instructions/error dialog if missing from PATH.
- **Process Cancellation:** Support canceling analysis or export tasks cleanly without freezing GUI.

---

## 6. Verification Criteria

- [ ] Select sample video with pauses.
- [ ] VAD accurately identifies speech vs silence timestamps.
- [ ] Timeline visual matches audio waveform / actual speech points.
- [ ] Video preview scrubbing works smoothly.
- [ ] Export produces valid MP4 containing only speech segments without audio/video drift.
