from __future__ import annotations

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QButtonGroup,
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class NavigationRail(QFrame):
    section_changed = pyqtSignal(str)

    def __init__(self, items: list[tuple[str, str]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("navigationRail")
        self.setFixedWidth(260)

        self._buttons: dict[str, QPushButton] = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 24, 18, 24)
        layout.setSpacing(12)

        brand = QLabel("Oficina 39")
        brand.setObjectName("brandTitle")
        layout.addWidget(brand)

        caption = QLabel("Desktop nativo")
        caption.setObjectName("brandCaption")
        layout.addWidget(caption)
        layout.addSpacing(20)

        for key, label in items:
            button = QPushButton(label)
            button.setCheckable(True)
            button.setProperty("navKey", key)
            button.clicked.connect(lambda checked=False, nav_key=key: self.section_changed.emit(nav_key))
            layout.addWidget(button)
            self._group.addButton(button)
            self._buttons[key] = button

        layout.addStretch(1)

        footer = QLabel(
            "Nova estrutura pronta para receber telas PyQt5 usando o dominio atual."
        )
        footer.setWordWrap(True)
        footer.setObjectName("railFooter")
        layout.addWidget(footer)

        self.apply_theme("escuro")

    def apply_theme(self, theme_mode: str) -> None:
        if theme_mode == "claro":
            stylesheet = """
                #navigationRail {
                    background: #eef3f8;
                    border-right: 1px solid #cfd9e3;
                }
                #brandTitle {
                    color: #16344c;
                    font-size: 24px;
                    font-weight: 700;
                }
                #brandCaption {
                    color: #456882;
                    font-size: 13px;
                }
                QPushButton {
                    text-align: left;
                    padding: 14px 16px;
                    border: 1px solid transparent;
                    border-radius: 12px;
                    background: transparent;
                    color: #2c4b63;
                    font-size: 14px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #dde8f2;
                    border: 1px solid #c3d3e3;
                }
                QPushButton:checked {
                    background: #2a6db0;
                    color: #ffffff;
                    border: 1px solid #347dca;
                }
                #railFooter {
                    color: #5f768c;
                    font-size: 12px;
                }
            """
        else:
            stylesheet = """
                #navigationRail {
                    background: #0b1016;
                    border-right: 1px solid #1f2b37;
                }
                #brandTitle {
                    color: #f5f8fb;
                    font-size: 24px;
                    font-weight: 700;
                }
                #brandCaption {
                    color: #7fa8c7;
                    font-size: 13px;
                }
                QPushButton {
                    text-align: left;
                    padding: 14px 16px;
                    border: 1px solid transparent;
                    border-radius: 12px;
                    background: transparent;
                    color: #b9cad9;
                    font-size: 14px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #121b24;
                    border: 1px solid #223140;
                }
                QPushButton:checked {
                    background: #2a6db0;
                    color: #ffffff;
                    border: 1px solid #347dca;
                }
                #railFooter {
                    color: #7f93a5;
                    font-size: 12px;
                }
            """
        self.setStyleSheet(stylesheet)

    def set_current(self, key: str) -> None:
        button = self._buttons.get(key)
        if button:
            button.setChecked(True)
            self.section_changed.emit(key)
