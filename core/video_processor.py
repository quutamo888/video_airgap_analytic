import os
import subprocess
import tempfile
from typing import List, Dict, Callable, Optional
from core.paths import get_ffmpeg_path

def build_ffmpeg_filter_complex(segments: List[Dict[str, float]]) -> str:
    """
    Builds FFmpeg filter_complex string to trim and concat video/audio segments.
    Applies aresample and asetpts to ensure continuous, clean audio timestamps
    without AAC timestamp gaps or skipped samples.
    """
    v_filters = []
    a_filters = []
    concat_inputs = []

    for i, seg in enumerate(segments):
        s = seg["start"]
        e = seg["end"]
        v_filters.append(f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[v{i}];\n")
        a_filters.append(f"[0:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS[a{i}];\n")
        concat_inputs.append(f"[v{i}][a{i}]")

    concat_filter = f"{''.join(concat_inputs)}concat=n={len(segments)}:v=1:a=1[catv][cata];\n"
    post_filter = "[catv]setpts=PTS-STARTPTS[outv];[cata]aresample=async=1000,asetpts=N/SR/TB[outa]"
    return "".join(v_filters) + "".join(a_filters) + concat_filter + post_filter

def cut_and_merge_video(
    video_path: str,
    speech_segments: List[Dict[str, float]],
    output_path: str,
    progress_callback: Optional[Callable[[float], None]] = None
) -> None:
    """
    Trims dead air and merges the speech segments into a new MP4 video.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Source video not found: {video_path}")
    if not speech_segments:
        raise ValueError("No speech segments provided to cut.")

    filter_complex = build_ffmpeg_filter_complex(speech_segments)

    ffmpeg_bin = get_ffmpeg_path()
    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", video_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-max_muxing_queue_size", "2048",
        "-avoid_negative_ts", "make_zero",
        output_path
    ]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        _, stderr = process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg slicing and merging failed: {stderr}")

        if progress_callback:
            progress_callback(100.0)
    finally:
        pass
