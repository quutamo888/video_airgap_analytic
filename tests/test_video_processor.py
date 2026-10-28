import pytest
from core.video_processor import build_ffmpeg_filter_complex

def test_build_filter_complex_single_segment():
    segments = [{"start": 1.0, "end": 4.0}]
    filter_str = build_ffmpeg_filter_complex(segments)
    assert "[0:v]trim=start=1.0:end=4.0,setpts=PTS-STARTPTS[v0];" in filter_str
    assert "[0:a]atrim=start=1.0:end=4.0,asetpts=PTS-STARTPTS[a0];" in filter_str
    assert "[v0][a0]concat=n=1:v=1:a=1[catv][cata];" in filter_str
    assert "[cata]aresample=async=1000,asetpts=N/SR/TB[outa]" in filter_str

def test_build_filter_complex_multiple_segments():
    segments = [{"start": 1.0, "end": 2.0}, {"start": 5.0, "end": 7.0}]
    filter_str = build_ffmpeg_filter_complex(segments)
    assert "[v0][a0][v1][a1]concat=n=2:v=1:a=1[catv][cata];" in filter_str
    assert "[cata]aresample=async=1000,asetpts=N/SR/TB[outa]" in filter_str
