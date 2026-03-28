from __future__ import annotations

from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class PlaceholderScreen(QWidget):
    def __init__(self, title: str, description: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        card = QFrame()
        card.setObjectName("screenCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("screenTitle")

        text_label = QLabel(description)
        text_label.setWordWrap(True)
        text_label.setObjectName("screenText")

        migration_label = QLabel(
            "Proxima etapa: ligar esta tela aos casos de uso do dominio e substituir os fluxos web equivalentes."
        )
        migration_label.setWordWrap(True)
        migration_label.setObjectName("screenText")

        card_layout.addWidget(title_label)
        card_layout.addWidget(text_label)
        card_layout.addWidget(migration_label)
        layout.addWidget(card)
