from __future__ import annotations

from PyQt5.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget


class DashboardScreen(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        hero = QFrame()
        hero.setObjectName("screenCard")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(24, 24, 24, 24)
        hero_layout.setSpacing(10)

        title = QLabel("Migracao para desktop nativo")
        title.setObjectName("screenTitle")

        text = QLabel(
            "Esta base inicial usa PyQt5 puro e preserva a camada de dominio existente. "
            "A partir daqui, cada tela pode ser migrada gradualmente sem depender de HTML, CSS, "
            "JavaScript ou navegador embutido."
        )
        text.setWordWrap(True)
        text.setObjectName("screenText")

        badge = QLabel("Camadas preparadas: ui, services, repositories, infrastructure")
        badge.setObjectName("badge")

        hero_layout.addWidget(title)
        hero_layout.addWidget(text)
        hero_layout.addWidget(badge)

        layout.addWidget(hero)
        layout.addWidget(self._build_cards())
        layout.addStretch(1)

    def _build_cards(self) -> QWidget:
        wrapper = QWidget()
        grid = QGridLayout(wrapper)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)

        cards = [
            ("Dominio", "Models, repositories e services atuais podem continuar como base."),
            ("Bootstrap", "Inicializacao desktop separada da interface web durante a transicao."),
            ("UI Nativa", "Janela principal, navegação e telas novas em PyQt5 puro."),
            ("Migracao", "Web legado e desktop novo convivem sem remocao imediata."),
        ]

        for index, (title, description) in enumerate(cards):
            card = QFrame()
            card.setObjectName("screenCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 20, 20, 20)
            card_layout.setSpacing(8)

            card_title = QLabel(title)
            card_title.setObjectName("screenTitle")
            card_text = QLabel(description)
            card_text.setWordWrap(True)
            card_text.setObjectName("screenText")

            card_layout.addWidget(card_title)
            card_layout.addWidget(card_text)
            grid.addWidget(card, index // 2, index % 2)

        return wrapper
