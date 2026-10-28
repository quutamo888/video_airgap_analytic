import os
import wave
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

    def __init__(self, video_path: str, speech_pad_sec: float, min_silence_sec: float, threshold: float = 0.5):
        super().__init__()
        self.video_path = video_path
        self.speech_pad_sec = speech_pad_sec
        self.min_silence_sec = min_silence_sec
        self.threshold = threshold

    def run(self):
        wav_path = None
        try:
            wav_path = extract_audio_16k_mono(self.video_path)
            detector = VadDetector()
            raw_segments = detector.detect_speech_segments(wav_path, threshold=self.threshold)

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
        self.resize(1000, 720)

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
        self.lbl_file.setStyleSheet("color: #888;")
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

        param_layout.addWidget(QLabel("VAD Threshold:"))
        self.spin_threshold = QDoubleSpinBox()
        self.spin_threshold.setRange(0.05, 0.95)
        self.spin_threshold.setSingleStep(0.05)
        self.spin_threshold.setValue(0.50)
        self.spin_threshold.setToolTip("Speech probability threshold. Lower (e.g. 0.3) detects soft speech.")
        param_layout.addWidget(self.spin_threshold)

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
        self.btn_export.setStyleSheet("""
            QPushButton:enabled {
                background-color: #2d8a4e;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:disabled {
                background-color: #444444;
                color: #888888;
                font-weight: normal;
                padding: 6px 12px;
                border-radius: 4px;
            }
        """)
        self.btn_export.clicked.connect(self.start_export)
        param_layout.addWidget(self.btn_export)

        layout.addWidget(param_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.mkv *.mov)")
        if file_path:
            self.current_video_path = file_path
            self.lbl_file.setText(os.path.basename(file_path))
            self.lbl_file.setStyleSheet("color: #000; font-weight: bold;")
            self.player_widget.load_media(file_path)
            self.btn_analyze.setEnabled(True)
            self.btn_export.setEnabled(False)
            self.timeline.set_segments([], [])

    def start_analysis(self):
        if not self.current_video_path:
            return
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(True)
        self.btn_analyze.setEnabled(False)
        self.btn_open.setEnabled(False)

        self.worker = AnalyzeWorker(
            video_path=self.current_video_path,
            speech_pad_sec=self.spin_padding.value(),
            min_silence_sec=self.spin_silence.value(),
            threshold=self.spin_threshold.value()
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

        has_speech = len(plan["speech_segments"]) > 0
        self.btn_export.setEnabled(has_speech)

        if not has_speech:
            QMessageBox.warning(
                self,
                "No Speech Detected",
                "ตรวจไม่พบช่วงเสียงพูดในคลิปนี้เลย (ทั้งคลิปกลายเป็น Dead Air / สีแดงทั้งหมด)\n\n"
                "วิธีแก้:\n"
                "1. ปรับลดค่า VAD Threshold ลง (เช่น 0.20 - 0.30) แล้วกด Analyze Dead Air ใหม่อีกครั้ง\n"
                "2. ตรวจสอบว่าในไฟล์มีเสียงพูดของมนุษย์หรือไม่ (Silero VAD ถูกเทรนมาจับเสียงพูดคนโดยเฉพาะ)"
            )
        else:
            cut_count = len(plan["dead_air_segments"])
            total_cut_duration = sum(s["end"] - s["start"] for s in plan["dead_air_segments"])
            QMessageBox.information(
                self,
                "Analysis Complete",
                f"วิเคราะห์เสร็จสิ้น!\n"
                f"- พบช่วงเสียงพูดที่เก็บไว้ (สีเขียว): {len(plan['speech_segments'])} ช่วง\n"
                f"- พบช่วง Dead Air ที่จะตัดออก (สีแดง): {cut_count} ช่วง ({total_cut_duration:.2f} วินาที)"
            )

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
