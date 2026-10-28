from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import QWidget
from typing import List, Dict

class TimelineWidget(QWidget):
    seekRequested = Signal(float)  # timestamp in seconds

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

        # Background
        painter.fillRect(self.rect(), QColor("#222222"))

        if self.duration <= 0:
            return

        w = self.width()
        h = self.height()

        # Draw dead air segments (red/gray)
        painter.setBrush(QBrush(QColor("#802d2d")))
        painter.setPen(Qt.NoPen)
        for seg in self.dead_air_segments:
            x1 = self.time_to_x(seg["start"])
            x2 = self.time_to_x(seg["end"])
            painter.drawRect(x1, 4, max(1, x2 - x1), h - 8)

        # Draw speech segments (vibrant green)
        painter.setBrush(QBrush(QColor("#2d8a4e")))
        for seg in self.speech_segments:
            x1 = self.time_to_x(seg["start"])
            x2 = self.time_to_x(seg["end"])
            painter.drawRect(x1, 4, max(1, x2 - x1), h - 8)

        # Draw current position needle
        head_x = self.time_to_x(self.current_pos)
        pen = QPen(QColor("#ffffff"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(head_x, 0, head_x, h)
