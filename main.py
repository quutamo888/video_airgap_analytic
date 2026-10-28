import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow
from core.paths import get_ffmpeg_path

def main():
    app = QApplication(sys.argv)

    # Check FFmpeg dependency (bundled or system PATH)
    try:
        get_ffmpeg_path()
    except Exception:
        QMessageBox.critical(
            None,
            "FFmpeg Missing",
            "FFmpeg was not found bundled with the app or in your system PATH.\nPlease install FFmpeg to use this application."
        )
        sys.exit(1)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
