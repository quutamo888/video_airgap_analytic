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
    from core.paths import get_ffmpeg_path
    ffmpeg_path = get_ffmpeg_path()
    assert ffmpeg_path is not None, "ffmpeg must be installed or bundled and accessible"
