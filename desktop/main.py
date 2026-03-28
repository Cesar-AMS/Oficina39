import ctypes
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from desktop.bootstrap.database import bootstrap_legacy_context
from desktop.ui.main_window import MainWindow


APP_ID = "Oficina39.NativeDesktop"


def _configure_windows_identity() -> None:
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass


def _icon_path() -> str | None:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    icon_path = os.path.join(base_dir, "icone.ico")
    return icon_path if os.path.exists(icon_path) else None


def _build_application(argv: list[str]) -> QApplication:
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(argv)
    app.setApplicationName("Oficina 39")
    app.setApplicationDisplayName("Oficina 39")
    app.setOrganizationName("Oficina 39")
    app.setDesktopFileName(APP_ID)

    icon_path = _icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))

    return app


def main() -> int:
    _configure_windows_identity()
    bootstrap_legacy_context()

    app = _build_application(sys.argv)
    window = MainWindow()
    window.showMaximized()
    return app.exec_()
