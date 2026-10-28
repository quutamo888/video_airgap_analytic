from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

class VideoPlayerWidget(QWidget):
    positionChanged = Signal(float)   # timestamp in seconds
    durationChanged = Signal(float)   # total duration in seconds

    def __init__(self, parent=None):
        super().__init__(parent)

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)

        self.video_widget = QVideoWidget(self)
        self.player.setVideoOutput(self.video_widget)

        # Controls
        self.btn_play = QPushButton("Play")
        self.btn_play.setFixedWidth(80)
        self.btn_play.clicked.connect(self.toggle_playback)

        self.lbl_time = QLabel("00:00 / 00:00")

        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(self.btn_play)
        ctrl_layout.addWidget(self.lbl_time)
        ctrl_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.video_widget, stretch=1)
        layout.addLayout(ctrl_layout)

        # Wire media player signals
        self.player.positionChanged.connect(self._on_pos_changed)
        self.player.durationChanged.connect(self._on_dur_changed)

    def load_media(self, file_path: str):
        self.player.setSource(QUrl.fromLocalFile(file_path))
        self.btn_play.setText("Play")

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
