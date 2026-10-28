import os
import subprocess
import tempfile
import pytest
from core.audio_extractor import extract_audio_16k_mono
from core.timeline_planner import plan_cut_segments
from core.video_processor import cut_and_merge_video

def create_synthetic_test_video(output_mp4: str):
    # Generates a 6-second video: 2s tone, 2s silence, 2s tone
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

def test_full_pipeline_mocked():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_mp4 = os.path.join(tmpdir, "input.mp4")
        output_mp4 = os.path.join(tmpdir, "output.mp4")

        # Create test video with FFmpeg if available
        try:
            create_synthetic_test_video(input_mp4)
        except Exception:
            pytest.skip("FFmpeg not available or failed to generate test video")

        assert os.path.exists(input_mp4)

        wav_path = extract_audio_16k_mono(input_mp4)
        assert os.path.exists(wav_path)

        # Simulated speech intervals: [0.0 - 2.0] and [4.0 - 6.0]
        raw_segments = [{"start": 0.0, "end": 2.0}, {"start": 4.0, "end": 6.0}]
        plan = plan_cut_segments(raw_segments, total_duration=6.0, speech_pad_sec=0.1, min_silence_sec=0.5)

        assert len(plan["speech_segments"]) == 2
        assert len(plan["dead_air_segments"]) == 1

        cut_and_merge_video(input_mp4, plan["speech_segments"], output_mp4)
        assert os.path.exists(output_mp4)
        assert os.path.getsize(output_mp4) > 0
