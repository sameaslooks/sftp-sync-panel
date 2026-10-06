import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon

from gui.mainwindow import MainWindow
from gui.style import get_qss
import gui.theme as theme


def _app_icon() -> QIcon:
    """Locate icon.ico in PyInstaller bundle (_MEIPASS) or dev assets/."""
    candidates = [
        # PyInstaller 6+: data files live in _internal/ (_MEIPASS)
        os.path.join(getattr(sys, "_MEIPASS", ""), "icon.ico"),
        # PyInstaller <6: next to the exe
        os.path.join(os.path.dirname(sys.executable), "icon.ico"),
        # Dev mode: assets/ sibling of src/
        os.path.join(os.path.dirname(__file__), "..", "assets", "icon.ico"),
    ]
    for path in candidates:
        path = os.path.normpath(path)
        if os.path.isfile(path):
            return QIcon(path)
    return QIcon()


def _is_system_dark() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return value == 0
    except Exception:
        return False


def _set_appid() -> None:
    # Without this Windows groups the taskbar entry under python.exe's icon.
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "kosmospace.sftp-sync-panel.1"
            )
        except Exception:
            pass


def main() -> None:
    _set_appid()
    app = QApplication(sys.argv)
    app.setApplicationName("SFTP Sync Panel")
    app.setStyle("Fusion")

    dark = _is_system_dark()
    theme.configure(dark)
    app.setStyleSheet(get_qss(dark))

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    icon = _app_icon()
    app.setWindowIcon(icon)

    window = MainWindow()
    window.setWindowIcon(icon)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
