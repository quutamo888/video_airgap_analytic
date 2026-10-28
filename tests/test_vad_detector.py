import pytest
import numpy as np
import wave
import tempfile
import os
from unittest.mock import MagicMock, patch
from core.vad_detector import VadDetector

def create_synthetic_wav(filename: str, duration_sec: float = 1.0, silence: bool = True):
    sample_rate = 16000
    total_samples = int(sample_rate * duration_sec)
    data = np.zeros(total_samples, dtype=np.int16) if silence else np.ones(total_samples, dtype=np.int16) * 1000

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(data.tobytes())

def test_vad_mocked_inference():
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_wav = f.name
    try:
        create_synthetic_wav(temp_wav, duration_sec=1.0, silence=True)
        with patch("onnxruntime.InferenceSession") as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session
            # Return low probability (silence)
            mock_session.run.return_value = (np.array([[0.05]], dtype=np.float32), np.zeros((2, 1, 128), dtype=np.float32))

            detector = VadDetector(model_path="dummy_model.onnx")
            segments = detector.detect_speech_segments(temp_wav, threshold=0.5)
            assert len(segments) == 0
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
