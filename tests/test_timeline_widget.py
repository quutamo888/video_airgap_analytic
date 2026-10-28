import pytest
from PySide6.QtCore import Qt
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

def test_timeline_segments_setting(qapp):
    widget = TimelineWidget()
    speech = [{"start": 1.0, "end": 2.0}]
    dead_air = [{"start": 2.0, "end": 4.0}]
    widget.set_segments(speech, dead_air)
    assert widget.speech_segments == speech
    assert widget.dead_air_segments == dead_air
