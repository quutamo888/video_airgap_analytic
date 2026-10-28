import os
import sys
import shutil
import subprocess

def find_system_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if path and os.path.isfile(path):
        return path
    # Look in common AppData winget paths
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        winget_link = os.path.join(local_app_data, "Microsoft", "WindowsApps", "ffmpeg.exe")
        if os.path.isfile(winget_link):
            return winget_link
    return ""

def main():
    root_dir = os.path.abspath(os.path.dirname(__file__))
    bin_dir = os.path.join(root_dir, "bin")
    os.makedirs(bin_dir, exist_ok=True)

    dest_ffmpeg = os.path.join(bin_dir, "ffmpeg.exe")
    if not os.path.isfile(dest_ffmpeg):
        src_ffmpeg = find_system_ffmpeg()
        if not src_ffmpeg:
            print("[ERROR] ffmpeg.exe not found on system to bundle.")
            sys.exit(1)
        print(f"Copying FFmpeg from {src_ffmpeg} to {dest_ffmpeg}...")
        shutil.copy2(src_ffmpeg, dest_ffmpeg)

    model_src = os.path.join(root_dir, "core", "models", "silero_vad.onnx")
    if not os.path.isfile(model_src):
        print("[ERROR] silero_vad.onnx not found in core/models/")
        sys.exit(1)

    print("Building Standalone Executable (One-Folder) with PyInstaller...")

    # Separator for PyInstaller --add-data on Windows is ';'
    sep = ";" if os.name == "nt" else ":"

    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        "--name", "VideoDeadAirCutter",
        f"--add-data={model_src}{sep}core/models",
        f"--add-data={dest_ffmpeg}{sep}bin",
        os.path.join(root_dir, "main.py")
    ]

    print("Running command:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=root_dir)
    if res.returncode != 0:
        print("[ERROR] PyInstaller failed.")
        sys.exit(res.returncode)

    dist_dir = os.path.join(root_dir, "dist", "VideoDeadAirCutter")
    print(f"\n[SUCCESS] Build completed! Distributable folder: {dist_dir}")

if __name__ == "__main__":
    main()
