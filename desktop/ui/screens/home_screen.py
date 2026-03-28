from __future__ import annotations

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from desktop.services.home_service import load_home_state
from desktop.ui.components.logo_card import LogoCard


class HomeScreen(QWidget):
    navigate_requested = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._state = load_home_state()
        self._logo_card = LogoCard()
        self._title_label = QLabel()
        self._company_label = QLabel()
        self._contact_label = QLabel()
        self._details_label = QLabel()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.addWidget(self._build_hero_card(), 1)

        self._apply_state()

    def reload_state(self) -> None:
        self._state = load_home_state()
        self._apply_state()

    def _build_hero_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("screenCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(22)

        badge = QLabel("Tela inicial migrada para desktop nativo")
        badge.setObjectName("badge")

        self._title_label.setObjectName("homeHeroTitle")
        self._title_label.setWordWrap(True)

        self._company_label.setObjectName("homeCompanyTitle")

        self._contact_label.setObjectName("screenText")
        self._contact_label.setWordWrap(True)

        self._details_label.setObjectName("screenText")
        self._details_label.setWordWrap(True)

        hero_row = QHBoxLayout()
        hero_row.setContentsMargins(0, 0, 0, 0)
        hero_row.setSpacing(28)

        text_column = QVBoxLayout()
        text_column.setSpacing(12)
        text_column.addWidget(self._company_label)
        text_column.addWidget(self._title_label)
        text_column.addWidget(self._contact_label)
        text_column.addWidget(self._details_label)
        text_column.addStretch(1)

        hero_row.addWidget(self._logo_card, 0)
        hero_row.addLayout(text_column, 1)

        layout.addWidget(badge)
        layout.addLayout(hero_row)
        layout.addStretch(1)
        return card

    def _apply_state(self) -> None:
        state = self._state
        self._title_label.setText(state.title)
        self._company_label.setText(state.company_name or "Oficina 39")

        contact_lines = []
        if state.company_phone:
            contact_lines.append(f"Contato: {state.company_phone}")
        if state.company_email:
            contact_lines.append(f"E-mail: {state.company_email}")
        if state.company_address:
            contact_lines.append(f"Endereco: {state.company_address}")
        if not contact_lines:
            contact_lines.append("Personalizacao carregada a partir da configuracao atual do sistema.")
        self._contact_label.setText("\n".join(contact_lines))

        self._details_label.setText(
            "Base desktop nativa carregando branding e dados reais da empresa diretamente da configuracao do sistema."
        )

        self._logo_card.update_logo(
            image_path=state.logo_path,
            shape=state.logo_shape,
            scale=state.logo_scale,
            offset_x=state.logo_offset_x,
            offset_y=state.logo_offset_y,
        )
