import os
import sys
import shutil

def get_base_dir() -> str:
    """
    Returns the base directory for resources.
    Supports PyInstaller frozen app (both onefile sys._MEIPASS and onedir sys.executable)
    as well as regular development mode.
    """
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            return sys._MEIPASS
        return os.path.dirname(sys.executable)
    # Repo root: parent of core/
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_resource_path(relative_path: str) -> str:
    """
    Returns the absolute path to a resource relative to the base directory.
    """
    return os.path.join(get_base_dir(), relative_path)

def get_ffmpeg_path() -> str:
    """
    Finds the FFmpeg executable path.
    Prioritizes bundled binary, then falls back to system PATH.
    """
    # 1. Check bundled in bin/
    candidate = get_resource_path(os.path.join("bin", "ffmpeg.exe" if os.name == "nt" else "ffmpeg"))
    if os.path.isfile(candidate):
        return candidate

    # 2. Check bundled in root dir (onedir root)
    candidate_root = get_resource_path("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if os.path.isfile(candidate_root):
        return candidate_root

    # 3. Fallback to system PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    raise FileNotFoundError("FFmpeg executable could not be found bundled or in system PATH.")
