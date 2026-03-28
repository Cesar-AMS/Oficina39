from __future__ import annotations

from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class SummaryCard(QFrame):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("summaryCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        self._value_label = QLabel("0")
        self._value_label.setObjectName("summaryValue")

        self._title_label = QLabel(title)
        self._title_label.setObjectName("summaryTitle")
        self._title_label.setWordWrap(True)

        layout.addWidget(self._value_label)
        layout.addWidget(self._title_label)

    def set_value(self, value: int) -> None:
        self._value_label.setText(str(value))
