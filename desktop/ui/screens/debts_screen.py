from __future__ import annotations

from functools import partial

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop.services.debts_service import build_debts_summary, list_open_debts
from desktop.ui.components.summary_card import SummaryCard
from desktop.ui.screens.finalize_order_dialog import FinalizeOrderDialog
from desktop.ui.screens.view_order_dialog import ViewOrderDialog


def _money(value: float) -> str:
    amount = float(value or 0)
    text = f"{amount:,.2f}"
    return f"R$ {text}".replace(",", "X").replace(".", ",").replace("X", ".")


def _text(value) -> str:
    cleaned = "" if value is None else str(value).strip()
    return cleaned or "---"


class DebtsScreen(QWidget):
    navigate_requested = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._items: list[dict] = []
        self._search_input = QLineEdit()
        self._table = QTableWidget(0, 8)
        self._summary_cards: dict[str, SummaryCard] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(18)

        root.addWidget(self._build_header())
        root.addWidget(self._build_filters_card())
        root.addWidget(self._build_summary_row())
        root.addWidget(self._build_table_card(), 1)

        self._configure_table()
        self.reload_debts()

    def _build_header(self) -> QWidget:
        card = QFrame()
        card.setObjectName("screenCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        texts = QVBoxLayout()
        title = QLabel("Debitos em aberto")
        title.setObjectName("screenTitle")
        subtitle = QLabel(
            "Acompanhe ordens com saldo pendente e abra direto o fluxo de recebimento no caixa."
        )
        subtitle.setObjectName("screenText")
        subtitle.setWordWrap(True)
        texts.addWidget(title)
        texts.addWidget(subtitle)

        back_button = QPushButton("Voltar ao inicio")
        back_button.clicked.connect(lambda: self.navigate_requested.emit("home"))

        layout.addLayout(texts, 1)
        layout.addWidget(back_button)
        return card

    def _build_filters_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("screenCard")
        layout = QGridLayout(card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(10)

        self._search_input.setPlaceholderText("Buscar por nome, CPF ou placa")
        self._search_input.returnPressed.connect(self.reload_debts)

        search_button = QPushButton("Buscar")
        search_button.clicked.connect(self.reload_debts)
        clear_button = QPushButton("Limpar")
        clear_button.clicked.connect(self._clear_filters)

        layout.addWidget(QLabel("Busca"), 0, 0)
        layout.addWidget(self._search_input, 1, 0)
        layout.addWidget(search_button, 1, 1)
        layout.addWidget(clear_button, 1, 2)
        layout.setColumnStretch(0, 1)
        return card

    def _build_summary_row(self) -> QWidget:
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        items = [
            ("total_ordens", "Ordens com debito"),
            ("total_em_aberto", "Em aberto"),
            ("total_parcial", "Parciais"),
            ("saldo_total", "Saldo total"),
        ]
        for key, title in items:
            card = SummaryCard(title)
            self._summary_cards[key] = card
            layout.addWidget(card, 1)
        return wrapper

    def _build_table_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("screenCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.addWidget(self._table)
        return card

    def _configure_table(self) -> None:
        self._table.setHorizontalHeaderLabels(
            ["OS", "Cliente", "Veiculo", "Total", "Pago", "Saldo", "Status financeiro", "Acoes"]
        )
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        header = self._table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, header.ResizeToContents)
        header.setSectionResizeMode(1, header.Stretch)
        header.setSectionResizeMode(2, header.Stretch)
        header.setSectionResizeMode(3, header.ResizeToContents)
        header.setSectionResizeMode(4, header.ResizeToContents)
        header.setSectionResizeMode(5, header.ResizeToContents)
        header.setSectionResizeMode(6, header.ResizeToContents)
        header.setSectionResizeMode(7, header.ResizeToContents)
        self._table.itemDoubleClicked.connect(self._handle_double_click)

    def _clear_filters(self) -> None:
        self._search_input.clear()
        self.reload_debts()

    def reload_debts(self) -> None:
        try:
            self._items = list_open_debts(self._search_input.text().strip())
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar debitos.\n\n{exc}")
            self._items = []
        self._refresh_summary()
        self._populate_table()

    def _refresh_summary(self) -> None:
        summary = build_debts_summary(self._items)
        self._summary_cards["total_ordens"].set_value(summary.total_ordens)
        self._summary_cards["total_em_aberto"].set_value(summary.total_em_aberto)
        self._summary_cards["total_parcial"].set_value(summary.total_parcial)
        self._summary_cards["saldo_total"].set_value(_money(summary.saldo_total))

    def _populate_table(self) -> None:
        self._table.setRowCount(len(self._items))

        for row, item in enumerate(self._items):
            client = item.get("cliente") or {}
            vehicle = " ".join(
                filter(
                    None,
                    [
                        _text(client.get("fabricante")) if client.get("fabricante") else "",
                        _text(client.get("modelo")) if client.get("modelo") else "",
                        f"- {_text(client.get('placa'))}" if client.get("placa") else "",
                    ],
                )
            ).strip() or "---"
            values = [
                f"#{item.get('id')}",
                _text(item.get("cliente_nome")),
                vehicle,
                _money(float(item.get("total_cobrado") or item.get("total_geral") or 0)),
                _money(float(item.get("total_pago") or 0)),
                _money(float(item.get("saldo_pendente") or 0)),
                _text(item.get("status_financeiro")),
            ]
            for col, value in enumerate(values):
                table_item = QTableWidgetItem(value)
                if col == 0:
                    table_item.setData(Qt.UserRole, item.get("id"))
                    table_item.setTextAlignment(Qt.AlignCenter)
                elif col in {3, 4, 5, 6}:
                    table_item.setTextAlignment(Qt.AlignCenter)
                self._table.setItem(row, col, table_item)

            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(6)

            receive_button = QPushButton("Receber")
            receive_button.clicked.connect(partial(self._open_cashier, int(item["id"])))
            view_button = QPushButton("Ver OS")
            view_button.clicked.connect(partial(self._open_view, int(item["id"])))
            actions_layout.addWidget(receive_button)
            actions_layout.addWidget(view_button)
            self._table.setCellWidget(row, 7, actions)

        if not self._items:
            self._table.setRowCount(1)
            placeholder = QTableWidgetItem("Nenhum debito em aberto.")
            placeholder.setFlags(Qt.ItemIsEnabled)
            placeholder.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(0, 0, placeholder)
            self._table.setSpan(0, 0, 1, 7)
            self._table.setCellWidget(0, 7, QWidget())

    def _selected_order_id(self, row: int) -> int | None:
        item = self._table.item(row, 0)
        if not item:
            return None
        data = item.data(Qt.UserRole)
        return int(data) if data else None

    def _handle_double_click(self, item: QTableWidgetItem) -> None:
        order_id = self._selected_order_id(item.row())
        if order_id:
            self._open_view(order_id)

    def _open_view(self, order_id: int) -> None:
        try:
            dialog = ViewOrderDialog(order_id, self)
            dialog.exec_()
            if getattr(dialog, "was_updated", False):
                self.reload_debts()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao abrir a OS.\n\n{exc}")

    def _open_cashier(self, order_id: int) -> None:
        dialog = FinalizeOrderDialog(order_id, self)
        if dialog.exec_():
            self.reload_debts()
