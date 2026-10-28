import os
import wave
import pytest
from core.audio_extractor import extract_audio_16k_mono

def test_extract_audio_fails_on_missing_file():
    with pytest.raises(FileNotFoundError):
        extract_audio_16k_mono("non_existent_file_path_12345.mp4")
