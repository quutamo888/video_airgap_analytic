# Video Dead Air Cutter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a desktop GUI application using PySide6 and Silero VAD (ONNX) to detect dead air / silence in MP4 video files, visualize the segments on an interactive timeline with video preview, and export a trimmed MP4.

**Architecture:** Python application with a modular separation between media/VAD core (`core/`) and PySide6 UI (`ui/`). Audio extraction, VAD detection, and final video slicing/concatenation use FFmpeg CLI and ONNX Runtime; long-running operations run on worker threads (`QThread`) to keep UI responsive.

**Tech Stack:** Python 3.10+, PySide6, onnxruntime, numpy, ffmpeg-python or direct ffmpeg subprocess, pytest.

## Global Constraints

- Platform: Windows 10/11 (Python 3.10+)
- VAD Engine: Silero VAD ONNX model (`silero_vad.onnx`) without PyTorch dependency
- Media Engine: System FFmpeg CLI executable must be detected or referenced
- UI: PySide6 (Qt6) `QMediaPlayer` + `QVideoWidget` + Custom `TimelineWidget`

---

### Task 1: Environment and Dependencies Setup

**Files:**
- Create: `requirements.txt`
- Create: `tests/conftest.py`
- Test: `tests/test_env.py`

**Interfaces:**
- Produces: Base project structure and dependency definitions (`onnxruntime`, `numpy`, `PySide6`, `pytest`).

- [ ] **Step 1: Create `requirements.txt`**

```text
PySide6>=6.5.0
onnxruntime>=1.15.0
numpy>=1.24.0
pytest>=7.0.0
```

- [ ] **Step 2: Write test for dependencies and ffmpeg availability**

```python
# tests/test_env.py
import shutil
import pytest

def test_imports():
    import numpy as np
    import onnxruntime as ort
    from PySide6 import QtCore, QtWidgets, QtMultimedia, QtMultimediaWidgets
    assert np is not None
    assert ort is not None
    assert QtCore is not None

def test_ffmpeg_installed():
    ffmpeg_path = shutil.which("ffmpeg")
    assert ffmpeg_path is not None, "ffmpeg must be installed and accessible in PATH"
```

- [ ] **Step 3: Run test to verify dependencies status**

Run: `pytest tests/test_env.py -v`

- [ ] **Step 4: Create `tests/conftest.py`**

```python
# tests/conftest.py
import os
import sys

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
```

---

### Task 2: Core Audio Extractor

**Files:**
- Create: `core/audio_extractor.py`
- Test: `tests/test_audio_extractor.py`

**Interfaces:**
- Produces: `extract_audio_16k_mono(video_path: str, output_wav_path: str | None = None) -> str`
  - Extracts 16kHz, 1-channel (mono), 16-bit PCM WAV from source video using `ffmpeg` subprocess.

- [ ] **Step 1: Write test for audio extractor**

```python
# tests/test_audio_extractor.py
import os
import wave
import pytest
from core.audio_extractor import extract_audio_16k_mono

def test_extract_audio_fails_on_missing_file():
    with pytest.raises(FileNotFoundError):
        extract_audio_16k_mono("non_existent_file.mp4")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_audio_extractor.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'core.audio_extractor'`)

- [ ] **Step 3: Implement `core/audio_extractor.py`**

```python
# core/audio_extractor.py
import os
import subprocess
import tempfile
from typing import Optional

def extract_audio_16k_mono(video_path: str, output_wav_path: Optional[str] = None) -> str:
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if output_wav_path is None:
        fd, output_wav_path = tempfile.mkstemp(suffix="_16k_mono.wav")
        os.close(fd)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        output_wav_path
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        if os.path.exists(output_wav_path):
            os.remove(output_wav_path)
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr}")

    return output_wav_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_audio_extractor.py -v`
Expected: PASS

---

### Task 3: Silero VAD Detector (ONNX)

**Files:**
- Create: `core/vad_detector.py`
- Test: `tests/test_vad_detector.py`

**Interfaces:**
- Produces: `VadDetector` class with method:
  `detect_speech_segments(wav_path: str, threshold: float = 0.5) -> list[dict[str, float]]`
  where each dict is `{"start": float, "end": float}` in seconds.

- [ ] **Step 1: Write test for VAD detector**

```python
# tests/test_vad_detector.py
import pytest
import numpy as np
import wave
import tempfile
import os
from core.vad_detector import VadDetector

def create_synthetic_wav(filename: str, duration_sec: float = 2.0, freq: float = 440.0, silence: bool = False):
    sample_rate = 16000
    total_samples = int(sample_rate * duration_sec)
    if silence:
        data = np.zeros(total_samples, dtype=np.int16)
    else:
        t = np.linspace(0, duration_sec, total_samples, endpoint=False)
        data = (np.sin(2 * np.pi * freq * t) * 32767 * 0.5).astype(np.int16)

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(data.tobytes())

def test_vad_init():
    detector = VadDetector()
    assert detector is not None

def test_vad_silence_detection():
    detector = VadDetector()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_wav = f.name
    try:
        create_synthetic_wav(temp_wav, duration_sec=1.0, silence=True)
        segments = detector.detect_speech_segments(temp_wav, threshold=0.5)
        assert len(segments) == 0
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_vad_detector.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'core.vad_detector'`)

- [ ] **Step 3: Implement `core/vad_detector.py` using ONNX runtime and Silero VAD model**

```python
# core/vad_detector.py
import os
import urllib.request
import wave
import numpy as np
import onnxruntime as ort
from typing import List, Dict

SILERO_VAD_ONNX_URL = "https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.onnx"

class VadDetector:
    def __init__(self, model_path: str | None = None):
        if model_path is None:
            models_dir = os.path.join(os.path.dirname(__file__), "models")
            os.makedirs(models_dir, exist_ok=True)
            model_path = os.path.join(models_dir, "silero_vad.onnx")
            if not os.path.exists(model_path):
                urllib.request.urlretrieve(SILERO_VAD_ONNX_URL, model_path)

        self.model_path = model_path
        opts = ort.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 1
        self.session = ort.InferenceSession(self.model_path, sess_options=opts, providers=["CPUExecutionProvider"])
        self.reset_states()

    def reset_states(self):
        self._state = np.zeros((2, 1, 128), dtype=np.float32)
        self._context = np.zeros((1, 64), dtype=np.float32)

    def _read_audio(self, wav_path: str) -> np.ndarray:
        with wave.open(wav_path, "rb") as wf:
            assert wf.getframerate() == 16000, "Sample rate must be 16kHz"
            assert wf.getnchannels() == 1, "Audio must be mono"
            assert wf.getsampwidth() == 2, "Audio must be 16-bit PCM"
            n_frames = wf.getnframes()
            audio_bytes = wf.readframes(n_frames)
            audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            return audio

    def detect_speech_segments(
        self,
        wav_path: str,
        threshold: float = 0.5,
        window_size_samples: int = 512
    ) -> List[Dict[str, float]]:
        self.reset_states()
        audio = self._read_audio(wav_path)
        sample_rate = 16000
        sr_tensor = np.array(sample_rate, dtype=np.int64)

        speech_probs = []
        for i in range(0, len(audio) - window_size_samples + 1, window_size_samples):
            chunk = audio[i : i + window_size_samples]
            x = np.expand_dims(chunk, 0)
            ort_inputs = {
                "input": x,
                "state": self._state,
                "sr": sr_tensor
            }
            ort_outs = self.session.run(None, ort_inputs)
            prob, self._state = ort_outs[0], ort_outs[1]
            speech_probs.append((i / sample_rate, float(prob[0][0])))

        segments = []
        in_speech = False
        start_time = 0.0

        for timestamp, prob in speech_probs:
            if prob >= threshold and not in_speech:
                in_speech = True
                start_time = timestamp
            elif prob < threshold and in_speech:
                in_speech = False
                segments.append({"start": round(start_time, 3), "end": round(timestamp, 3)})

        if in_speech:
            total_duration = len(audio) / sample_rate
            segments.append({"start": round(start_time, 3), "end": round(total_duration, 3)})

        return segments
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_vad_detector.py -v`
Expected: PASS

---

### Task 4: Timeline Planner for Speech & Dead Air Segments

**Files:**
- Create: `core/timeline_planner.py`
- Test: `tests/test_timeline_planner.py`

**Interfaces:**
- Produces: `plan_cut_segments(raw_segments: list[dict], total_duration: float, speech_pad_sec: float = 0.15, min_silence_sec: float = 0.5) -> dict`
  - Returns:
    ```python
    {
      "speech_segments": [{"start": float, "end": float}], # segments to keep
      "dead_air_segments": [{"start": float, "end": float}] # segments to cut
    }
    ```

- [ ] **Step 1: Write test for timeline planner**

```python
# tests/test_timeline_planner.py
from core.timeline_planner import plan_cut_segments

def test_empty_raw_segments():
    res = plan_cut_segments([], total_duration=10.0)
    assert len(res["speech_segments"]) == 0
    assert len(res["dead_air_segments"]) == 1
    assert res["dead_air_segments"][0] == {"start": 0.0, "end": 10.0}

def test_speech_padding_and_merging():
    # Two close speech segments: [1.0, 2.0] and [2.1, 3.0]
    # With pad 0.15, [1.0 - 0.15, 2.0 + 0.15] = [0.85, 2.15]
    # [2.1 - 0.15, 3.0 + 0.15] = [1.95, 3.15] -> Overlap! Merge into [0.85, 3.15]
    raw = [{"start": 1.0, "end": 2.0}, {"start": 2.1, "end": 3.0}]
    res = plan_cut_segments(raw, total_duration=5.0, speech_pad_sec=0.15, min_silence_sec=0.5)
    assert len(res["speech_segments"]) == 1
    assert res["speech_segments"][0]["start"] == 0.85
    assert res["speech_segments"][0]["end"] == 3.15
    assert len(res["dead_air_segments"]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_timeline_planner.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'core.timeline_planner'`)

- [ ] **Step 3: Implement `core/timeline_planner.py`**

```python
# core/timeline_planner.py
from typing import List, Dict, Any

def plan_cut_segments(
    raw_segments: List[Dict[str, float]],
    total_duration: float,
    speech_pad_sec: float = 0.15,
    min_silence_sec: float = 0.5
) -> Dict[str, Any]:
    if not raw_segments:
        return {
            "speech_segments": [],
            "dead_air_segments": [{"start": 0.0, "end": round(total_duration, 3)}] if total_duration > 0 else []
        }

    # 1. Apply padding to raw segments
    padded = []
    for seg in raw_segments:
        s = max(0.0, seg["start"] - speech_pad_sec)
        e = min(total_duration, seg["end"] + speech_pad_sec)
        padded.append({"start": round(s, 3), "end": round(e, 3)})

    # 2. Merge overlapping or touching segments
    padded.sort(key=lambda x: x["start"])
    merged = [padded[0]]
    for cur in padded[1:]:
        prev = merged[-1]
        if cur["start"] <= prev["end"]:
            prev["end"] = max(prev["end"], cur["end"])
        else:
            merged.append(cur)

    # 3. Calculate silence intervals between speech segments
    silences = []
    current_time = 0.0

    for speech in merged:
        if speech["start"] > current_time:
            silence_len = speech["start"] - current_time
            if silence_len >= min_silence_sec:
                silences.append({"start": round(current_time, 3), "end": round(speech["start"], 3)})
            else:
                # Silence is too short to cut; absorb into previous or current speech segment
                if merged and merged[0] != speech:
                    # Extend previous speech segment to cover this short pause
                    idx = merged.index(speech)
                    merged[idx - 1]["end"] = speech["start"]
        current_time = speech["end"]

    # Trailing silence
    if current_time < total_duration:
        trailing_len = total_duration - current_time
        if trailing_len >= min_silence_sec:
            silences.append({"start": round(current_time, 3), "end": round(total_duration, 3)})

    # Re-merge speech segments if short pauses were absorbed
    final_speech = []
    for seg in merged:
        if not final_speech:
            final_speech.append(seg)
        else:
            if seg["start"] <= final_speech[-1]["end"]:
                final_speech[-1]["end"] = max(final_speech[-1]["end"], seg["end"])
            else:
                final_speech.append(seg)

    return {
        "speech_segments": final_speech,
        "dead_air_segments": silences
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_timeline_planner.py -v`
Expected: PASS

---

### Task 5: Video Processor (Slicing & Concat)

**Files:**
- Create: `core/video_processor.py`
- Test: `tests/test_video_processor.py`

**Interfaces:**
- Produces: `cut_and_merge_video(video_path: str, speech_segments: list[dict], output_path: str, progress_callback=None) -> None`
  - Creates a concat filter FFmpeg command to export sliced segments into a single MP4 file.

- [ ] **Step 1: Write test for video processor command generation**

```python
# tests/test_video_processor.py
import pytest
from core.video_processor import build_ffmpeg_filter_complex

def test_build_filter_complex_single_segment():
    segments = [{"start": 1.0, "end": 4.0}]
    filter_str = build_ffmpeg_filter_complex(segments)
    assert "[0:v]trim=start=1.0:end=4.0,setpts=PTS-STARTPTS[v0];" in filter_str
    assert "[0:a]atrim=start=1.0:end=4.0,asetpts=PTS-STARTPTS[a0];" in filter_str
    assert "[v0][a0]concat=n=1:v=1:a=1[outv][outa]" in filter_str

def test_build_filter_complex_multiple_segments():
    segments = [{"start": 1.0, "end": 2.0}, {"start": 5.0, "end": 7.0}]
    filter_str = build_ffmpeg_filter_complex(segments)
    assert "concat=n=2:v=1:a=1[outv][outa]" in filter_str
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_video_processor.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'core.video_processor'`)

- [ ] **Step 3: Implement `core/video_processor.py`**

```python
# core/video_processor.py
import os
import subprocess
from typing import List, Dict, Callable, Optional

def build_ffmpeg_filter_complex(segments: List[Dict[str, float]]) -> str:
    v_filters = []
    a_filters = []
    concat_inputs = []

    for i, seg in enumerate(segments):
        s = seg["start"]
        e = seg["end"]
        v_filters.append(f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[v{i}];")
        a_filters.append(f"[0:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS[a{i}];")
        concat_inputs.append(f"[v{i}][a{i}]")

    concat_filter = f"{''.join(concat_inputs)}concat=n={len(segments)}:v=1:a=1[outv][outa]"
    return "".join(v_filters) + "".join(a_filters) + concat_filter

def cut_and_merge_video(
    video_path: str,
    speech_segments: List[Dict[str, float]],
    output_path: str,
    progress_callback: Optional[Callable[[float], None]] = None
) -> None:
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Source video not found: {video_path}")
    if not speech_segments:
        raise ValueError("No speech segments provided to cut.")

    filter_complex = build_ffmpeg_filter_complex(speech_segments)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    _, stderr = process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg slicing and merging failed: {stderr}")

    if progress_callback:
        progress_callback(100.0)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_video_processor.py -v`
Expected: PASS

---

### Task 6: UI Custom Timeline Widget

**Files:**
- Create: `ui/timeline_widget.py`
- Test: `tests/test_timeline_widget.py`

**Interfaces:**
- Produces: `TimelineWidget(QWidget)`
  - Signals: `seekRequested(float)` timestamp in seconds
  - Methods: `set_duration(duration: float)`, `set_segments(speech: list, dead_air: list)`, `set_current_position(pos: float)`
  - Displays green bars for speech, red/gray bars for dead air, and a needle indicator for playback head.

- [ ] **Step 1: Write test for timeline widget logic**

```python
# tests/test_timeline_widget.py
import pytest
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QApplication
from ui.timeline_widget import TimelineWidget

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_timeline_seek_calculation(qapp):
    widget = TimelineWidget()
    widget.resize(1000, 50)
    widget.set_duration(100.0)

    # Click in middle (x=500) -> 50.0 seconds
    timestamp = widget.x_to_time(500)
    assert abs(timestamp - 50.0) < 0.1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_timeline_widget.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'ui.timeline_widget'`)

- [ ] **Step 3: Implement `ui/timeline_widget.py`**

```python
# ui/timeline_widget.py
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import QWidget
from typing import List, Dict

class TimelineWidget(QWidget):
    seekRequested = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(48)
        self.duration = 0.0
        self.current_pos = 0.0
        self.speech_segments: List[Dict[str, float]] = []
        self.dead_air_segments: List[Dict[str, float]] = []

    def set_duration(self, duration: float):
        self.duration = max(0.0, duration)
        self.update()

    def set_current_position(self, pos: float):
        self.current_pos = max(0.0, min(pos, self.duration))
        self.update()

    def set_segments(self, speech: List[Dict[str, float]], dead_air: List[Dict[str, float]]):
        self.speech_segments = speech
        self.dead_air_segments = dead_air
        self.update()

    def x_to_time(self, x: int) -> float:
        if self.width() <= 0 or self.duration <= 0:
            return 0.0
        ratio = max(0.0, min(1.0, x / self.width()))
        return ratio * self.duration

    def time_to_x(self, t: float) -> int:
        if self.duration <= 0:
            return 0
        ratio = max(0.0, min(1.0, t / self.duration))
        return int(ratio * self.width())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            t = self.x_to_time(event.pos().x())
            self.seekRequested.emit(t)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            t = self.x_to_time(event.pos().x())
            self.seekRequested.emit(t)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background (empty / dead air)
        painter.fillRect(self.rect(), QColor("#2b2b2b"))

        if self.duration <= 0:
            return

        w = self.width()
        h = self.height()

        # Draw dead air segments in subtle red/gray
        painter.setBrush(QBrush(QColor("#782828")))
        painter.setPen(Qt.NoPen)
        for seg in self.dead_air_segments:
            x1 = self.time_to_x(seg["start"])
            x2 = self.time_to_x(seg["end"])
            painter.drawRect(x1, 4, max(1, x2 - x1), h - 8)

        # Draw speech segments in vibrant green
        painter.setBrush(QBrush(QColor("#2d8a4e")))
        for seg in self.speech_segments:
            x1 = self.time_to_x(seg["start"])
            x2 = self.time_to_x(seg["end"])
            painter.drawRect(x1, 4, max(1, x2 - x1), h - 8)

        # Draw playhead needle
        head_x = self.time_to_x(self.current_pos)
        pen = QPen(QColor("#ffffff"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(head_x, 0, head_x, h)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_timeline_widget.py -v`
Expected: PASS

---

### Task 7: UI Video Player Component

**Files:**
- Create: `ui/video_player.py`

**Interfaces:**
- Produces: `VideoPlayerWidget(QWidget)`
  - Integrates `QMediaPlayer`, `QAudioOutput`, `QVideoWidget`.
  - Exposes playback controls: Play, Pause, Seek, Duration signal, Position signal.

- [ ] **Step 1: Implement `ui/video_player.py`**

```python
# ui/video_player.py
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

class VideoPlayerWidget(QWidget):
    positionChanged = Signal(float)   # seconds
    durationChanged = Signal(float)   # seconds

    def __init__(self, parent=None):
        super().__init__(parent)

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)

        self.video_widget = QVideoWidget(self)
        self.player.setVideoOutput(self.video_widget)

        # Controls
        self.btn_play = QPushButton("Play")
        self.btn_play.clicked.connect(self.toggle_playback)

        self.lbl_time = QLabel("00:00 / 00:00")

        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(self.btn_play)
        ctrl_layout.addWidget(self.lbl_time)
        ctrl_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.addWidget(self.video_widget, stretch=1)
        layout.addLayout(ctrl_layout)

        # Wire media player signals
        self.player.positionChanged.connect(self._on_pos_changed)
        self.player.durationChanged.connect(self._on_dur_changed)

    def load_media(self, file_path: str):
        self.player.setSource(QUrl.fromLocalFile(file_path))

    def toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.btn_play.setText("Play")
        else:
            self.player.play()
            self.btn_play.setText("Pause")

    def seek_seconds(self, sec: float):
        ms = int(sec * 1000)
        self.player.setPosition(ms)

    def _on_pos_changed(self, pos_ms: int):
        sec = pos_ms / 1000.0
        self.positionChanged.emit(sec)
        self._update_time_label()

    def _on_dur_changed(self, dur_ms: int):
        sec = dur_ms / 1000.0
        self.durationChanged.emit(sec)
        self._update_time_label()

    def _update_time_label(self):
        pos_s = int(self.player.position() / 1000)
        dur_s = int(self.player.duration() / 1000)
        p_m, p_s = divmod(pos_s, 60)
        d_m, d_s = divmod(dur_s, 60)
        self.lbl_time.setText(f"{p_m:02d}:{p_s:02d} / {d_m:02d}:{d_s:02d}")
```

---

### Task 8: Main Window Orchestration & Entry Point

**Files:**
- Create: `ui/main_window.py`
- Create: `main.py`

**Interfaces:**
- Produces: `MainWindow` integrating file selection, background worker threads (`AnalyzeWorker`, `ExportWorker`), parameters controls (padding, silence threshold), `TimelineWidget`, `VideoPlayerWidget`.
- Produces: `main.py` entry point.

- [ ] **Step 1: Implement `ui/main_window.py` with QThread Workers**

```python
# ui/main_window.py
import os
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QSpinBox, QDoubleSpinBox, QProgressBar, QMessageBox, QGroupBox
)
from ui.video_player import VideoPlayerWidget
from ui.timeline_widget import TimelineWidget
from core.audio_extractor import extract_audio_16k_mono
from core.vad_detector import VadDetector
from core.timeline_planner import plan_cut_segments
from core.video_processor import cut_and_merge_video

class AnalyzeWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, video_path: str, speech_pad_sec: float, min_silence_sec: float):
        super().__init__()
        self.video_path = video_path
        self.speech_pad_sec = speech_pad_sec
        self.min_silence_sec = min_silence_sec

    def run(self):
        wav_path = None
        try:
            wav_path = extract_audio_16k_mono(self.video_path)
            detector = VadDetector()
            raw_segments = detector.detect_speech_segments(wav_path)

            import wave
            with wave.open(wav_path, "rb") as wf:
                duration = wf.getnframes() / float(wf.getframerate())

            plan = plan_cut_segments(
                raw_segments=raw_segments,
                total_duration=duration,
                speech_pad_sec=self.speech_pad_sec,
                min_silence_sec=self.min_silence_sec
            )
            plan["duration"] = duration
            self.finished.emit(plan)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            if wav_path and os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except OSError:
                    pass

class ExportWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, video_path: str, speech_segments: list, output_path: str):
        super().__init__()
        self.video_path = video_path
        self.speech_segments = speech_segments
        self.output_path = output_path

    def run(self):
        try:
            cut_and_merge_video(self.video_path, self.speech_segments, self.output_path)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Dead Air Cutter")
        self.resize(1000, 700)

        self.current_video_path = None
        self.analysis_result = None

        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Top Bar: File select & Actions
        top_layout = QHBoxLayout()
        self.btn_open = QPushButton("Open Video MP4")
        self.btn_open.clicked.connect(self.open_file)
        self.lbl_file = QLabel("No file loaded")
        self.btn_analyze = QPushButton("Analyze Dead Air")
        self.btn_analyze.setEnabled(False)
        self.btn_analyze.clicked.connect(self.start_analysis)

        top_layout.addWidget(self.btn_open)
        top_layout.addWidget(self.lbl_file)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_analyze)
        layout.addLayout(top_layout)

        # Video Player
        self.player_widget = VideoPlayerWidget(self)
        layout.addWidget(self.player_widget, stretch=1)

        # Timeline Widget
        self.timeline = TimelineWidget(self)
        layout.addWidget(self.timeline)

        # Connect Timeline & Player
        self.timeline.seekRequested.connect(self.player_widget.seek_seconds)
        self.player_widget.positionChanged.connect(self.timeline.set_current_position)
        self.player_widget.durationChanged.connect(self.timeline.set_duration)

        # Parameters & Export Controls
        param_group = QGroupBox("Detection & Trimming Settings")
        param_layout = QHBoxLayout(param_group)

        param_layout.addWidget(QLabel("Min Silence (sec):"))
        self.spin_silence = QDoubleSpinBox()
        self.spin_silence.setRange(0.1, 5.0)
        self.spin_silence.setSingleStep(0.1)
        self.spin_silence.setValue(0.5)
        param_layout.addWidget(self.spin_silence)

        param_layout.addWidget(QLabel("Speech Padding (sec):"))
        self.spin_padding = QDoubleSpinBox()
        self.spin_padding.setRange(0.0, 1.0)
        self.spin_padding.setSingleStep(0.05)
        self.spin_padding.setValue(0.15)
        param_layout.addWidget(self.spin_padding)

        param_layout.addStretch()

        self.btn_export = QPushButton("Export Trimmed Video")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self.start_export)
        param_layout.addWidget(self.btn_export)

        layout.addWidget(param_group)

        # Progress bar & Status
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.mkv *.mov)")
        if file_path:
            self.current_video_path = file_path
            self.lbl_file.setText(os.path.basename(file_path))
            self.player_widget.load_media(file_path)
            self.btn_analyze.setEnabled(True)
            self.btn_export.setEnabled(False)
            self.timeline.set_segments([], [])

    def start_analysis(self):
        if not self.current_video_path:
            return
        self.progress_bar.setRange(0, 0) # indeterminate
        self.progress_bar.setVisible(True)
        self.btn_analyze.setEnabled(False)
        self.btn_open.setEnabled(False)

        self.worker = AnalyzeWorker(
            video_path=self.current_video_path,
            speech_pad_sec=self.spin_padding.value(),
            min_silence_sec=self.spin_silence.value()
        )
        self.worker.finished.connect(self._on_analysis_finished)
        self.worker.error.connect(self._on_worker_error)
        self.worker.start()

    def _on_analysis_finished(self, plan: dict):
        self.progress_bar.setVisible(False)
        self.btn_analyze.setEnabled(True)
        self.btn_open.setEnabled(True)
        self.analysis_result = plan

        self.timeline.set_duration(plan["duration"])
        self.timeline.set_segments(plan["speech_segments"], plan["dead_air_segments"])
        self.btn_export.setEnabled(len(plan["speech_segments"]) > 0)

        cut_count = len(plan["dead_air_segments"])
        QMessageBox.information(self, "Analysis Complete", f"Identified {cut_count} dead air segment(s).")

    def _on_worker_error(self, err_msg: str):
        self.progress_bar.setVisible(False)
        self.btn_analyze.setEnabled(True)
        self.btn_open.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Operation failed: {err_msg}")

    def start_export(self):
        if not self.current_video_path or not self.analysis_result:
            return

        out_path, _ = QFileDialog.getSaveFileName(self, "Save Trimmed Video", "output_trimmed.mp4", "MP4 Files (*.mp4)")
        if not out_path:
            return

        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(True)
        self.btn_export.setEnabled(False)

        self.export_worker = ExportWorker(
            video_path=self.current_video_path,
            speech_segments=self.analysis_result["speech_segments"],
            output_path=out_path
        )
        self.export_worker.finished.connect(self._on_export_finished)
        self.export_worker.error.connect(self._on_worker_error)
        self.export_worker.start()

    def _on_export_finished(self, output_path: str):
        self.progress_bar.setVisible(False)
        self.btn_export.setEnabled(True)
        QMessageBox.information(self, "Export Complete", f"Trimmed video saved successfully to:\n{output_path}")
```

- [ ] **Step 2: Implement `main.py` entry point**

```python
# main.py
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

---

### Task 9: End-to-End Verification & User Testing

**Files:**
- Create: `tests/test_e2e_pipeline.py`

**Interfaces:**
- Verifies synthetic video generation with silence -> VAD analysis -> segment cutting -> export result.

- [ ] **Step 1: Write synthetic end-to-end integration test**

```python
# tests/test_e2e_pipeline.py
import os
import subprocess
import tempfile
import pytest
from core.audio_extractor import extract_audio_16k_mono
from core.vad_detector import VadDetector
from core.timeline_planner import plan_cut_segments
from core.video_processor import cut_and_merge_video

def create_synthetic_test_video(output_mp4: str):
    # Generates a 6-second video: 2s speech-like tone, 2s silence, 2s speech-like tone
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=320x240:d=6:r=24",
        "-f", "lavfi", "-i", "sine=f=440:d=2",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
        "-f", "lavfi", "-i", "sine=f=880:d=2",
        "-filter_complex",
        "[2:a]atrim=end=2[a_silence];[1:a][a_silence][3:a]concat=n=3:v=0:a=1[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "libx264", "-c:a", "aac",
        output_mp4
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def test_full_pipeline_synthetic():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_mp4 = os.path.join(tmpdir, "input.mp4")
        output_mp4 = os.path.join(tmpdir, "output.mp4")

        create_synthetic_test_video(input_mp4)
        assert os.path.exists(input_mp4)

        wav_path = extract_audio_16k_mono(input_mp4)
        assert os.path.exists(wav_path)

        detector = VadDetector()
        raw_segments = detector.detect_speech_segments(wav_path)

        plan = plan_cut_segments(raw_segments, total_duration=6.0, speech_pad_sec=0.1, min_silence_sec=0.5)
        assert len(plan["speech_segments"]) >= 1
        assert len(plan["dead_air_segments"]) >= 1

        cut_and_merge_video(input_mp4, plan["speech_segments"], output_mp4)
        assert os.path.exists(output_mp4)
        assert os.path.getsize(output_mp4) > 0
```

- [ ] **Step 2: Run end-to-end integration test**

Run: `pytest tests/test_e2e_pipeline.py -v`
Expected: PASS
