import os
import subprocess
import tempfile
from typing import Optional
from core.paths import get_ffmpeg_path

def extract_audio_16k_mono(video_path: str, output_wav_path: Optional[str] = None) -> str:
    """
    Extracts 16kHz mono PCM 16-bit audio WAV from a given video file using FFmpeg.
    Returns path to the extracted WAV file.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if output_wav_path is None:
        fd, output_wav_path = tempfile.mkstemp(suffix="_16k_mono.wav")
        os.close(fd)

    ffmpeg_bin = get_ffmpeg_path()
    cmd = [
        ffmpeg_bin,
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
            try:
                os.remove(output_wav_path)
            except OSError:
                pass
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr}")

    return output_wav_path
