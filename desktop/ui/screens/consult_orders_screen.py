from __future__ import annotations

from functools import partial

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
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

from desktop.services.orders_query_service import build_daily_summary, list_orders
from desktop.ui.components.summary_card import SummaryCard
from desktop.ui.screens.edit_order_dialog import EditOrderDialog
from desktop.ui.screens.finalize_order_dialog import FinalizeOrderDialog
from desktop.ui.screens.view_order_dialog import ViewOrderDialog


def _format_currency(value: float) -> str:
    amount = float(value or 0)
    text = f"{amount:,.2f}"
    return f"R$ {text}".replace(",", "X").replace(".", ",").replace("X", ".")


class ConsultOrdersScreen(QWidget):
    navigate_requested = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_status_alias = "todas"
        self._orders = []
        self._summary_cards: dict[str, SummaryCard] = {}

        self._search_input = QLineEdit()
        self._status_combo = QComboBox()
        self._table = QTableWidget(0, 9)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(18)

        root_layout.addWidget(self._build_header())
        root_layout.addWidget(self._build_filters_card())
        root_layout.addWidget(self._build_summary_row())
        root_layout.addWidget(self._build_table_card(), 1)

        self._apply_table_setup()
        self.reload_orders()

    def _build_header(self) -> QWidget:
        card = QFrame()
        card.setObjectName("screenCard")

        layout = QHBoxLayout(card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        texts = QVBoxLayout()
        texts.setSpacing(4)

        title = QLabel("Consultar Ordens")
        title.setObjectName("screenTitle")

        subtitle = QLabel(
            "Listagem nativa das ordens com busca, filtros, visualizacao completa da OS e edicao nativa."
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("screenText")
        texts.addWidget(title)
        texts.addWidget(subtitle)

        layout.addLayout(texts, 1)

        back_button = QPushButton("Voltar ao inicio")
        back_button.clicked.connect(lambda: self.navigate_requested.emit("home"))
        layout.addWidget(back_button)
        return card

    def _build_filters_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("screenCard")

        layout = QGridLayout(card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(12)

        search_label = QLabel("Nome ou CPF")
        search_label.setObjectName("screenText")
        self._search_input.setPlaceholderText("Digite o nome ou CPF do cliente")
        self._search_input.returnPressed.connect(self.reload_orders)

        status_label = QLabel("Status")
        status_label.setObjectName("screenText")
        self._status_combo.addItem("Todas", "todas")
        self._status_combo.addItem("Aguardando", "aguardando")
        self._status_combo.addItem("Em andamento", "andamento")
        self._status_combo.addItem("Concluido", "concluido")
        self._status_combo.addItem("Garantia", "garantia")
        self._status_combo.currentIndexChanged.connect(self.reload_orders)

        search_button = QPushButton("Buscar")
        search_button.clicked.connect(self.reload_orders)
        clear_button = QPushButton("Limpar")
        clear_button.clicked.connect(self._clear_filters)

        layout.addWidget(search_label, 0, 0)
        layout.addWidget(status_label, 0, 1)
        layout.addWidget(self._search_input, 1, 0)
        layout.addWidget(self._status_combo, 1, 1)
        layout.addWidget(search_button, 1, 2)
        layout.addWidget(clear_button, 1, 3)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 0)
        return card

    def _build_summary_row(self) -> QWidget:
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        items = [
            ("abertas", "Abertas (hoje)"),
            ("em_execucao", "Em execucao (hoje)"),
            ("concluidas", "Concluidas (hoje)"),
            ("total_dia", "Total do dia"),
            ("sem_profissional", "Sem profissional"),
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

    def _apply_table_setup(self) -> None:
        headers = ["ID", "Cliente", "Veiculo", "Placa", "Profissional", "Valor", "Status", "Entrada", "Acoes"]
        self._table.setHorizontalHeaderLabels(headers)
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
        header.setSectionResizeMode(8, header.ResizeToContents)
        self._table.itemDoubleClicked.connect(self._handle_row_double_click)

    def _clear_filters(self) -> None:
        self._search_input.clear()
        self._status_combo.setCurrentIndex(0)
        self.reload_orders()

    def reload_orders(self) -> None:
        self._current_status_alias = self._status_combo.currentData() or "todas"
        try:
            self._orders = list_orders(
                cliente_term=self._search_input.text().strip(),
                status_alias=self._current_status_alias,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar ordens.\n\n{exc}")
            self._orders = []
        self._refresh_summary()
        self._populate_table()

    def _refresh_summary(self) -> None:
        summary = build_daily_summary(self._orders)
        self._summary_cards["abertas"].set_value(summary.abertas)
        self._summary_cards["em_execucao"].set_value(summary.em_execucao)
        self._summary_cards["concluidas"].set_value(summary.concluidas)
        self._summary_cards["total_dia"].set_value(summary.total_dia)
        self._summary_cards["sem_profissional"].set_value(summary.sem_profissional)

    def _populate_table(self) -> None:
        self._table.clearSpans()
        self._table.setRowCount(len(self._orders))

        for row_index, order in enumerate(self._orders):
            values = [
                f"#{order.id}",
                order.cliente_nome,
                order.veiculo,
                order.placa,
                order.profissional,
                _format_currency(order.valor_total),
                order.status,
                order.data_entrada,
            ]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column_index in {0, 5, 6, 7}:
                    item.setTextAlignment(Qt.AlignCenter)
                if column_index == 0:
                    item.setData(Qt.UserRole, order.id)
                self._table.setItem(row_index, column_index, item)

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(6)

            details_button = QPushButton("Visualizar")
            details_button.clicked.connect(partial(self._open_details, order.id))
            edit_button = QPushButton("Editar")
            edit_button.clicked.connect(partial(self._open_edit_dialog, order.id))
            cashier_button = QPushButton("Caixa")
            cashier_button.clicked.connect(partial(self._open_cashier_dialog, order.id))

            actions_layout.addWidget(details_button)
            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(cashier_button)
            self._table.setCellWidget(row_index, 8, actions_widget)

        if not self._orders:
            self._table.setRowCount(1)
            for col in range(8):
                placeholder = QTableWidgetItem("" if col else "Nenhuma ordem encontrada")
                placeholder.setFlags(Qt.ItemIsEnabled)
                if col == 0:
                    placeholder.setTextAlignment(Qt.AlignCenter)
                self._table.setItem(0, col, placeholder)
            self._table.setSpan(0, 0, 1, 8)
            self._table.setCellWidget(0, 8, QWidget())

    def _get_order_id_from_row(self, row: int) -> int | None:
        item = self._table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.UserRole)

    def _handle_row_double_click(self, item: QTableWidgetItem) -> None:
        order_id = self._get_order_id_from_row(item.row())
        if order_id:
            self._open_details(order_id)

    def _open_details(self, order_id: int) -> None:
        try:
            dialog = ViewOrderDialog(order_id, self)
            dialog.exec_()
            if getattr(dialog, "was_updated", False):
                self.reload_orders()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao abrir a OS.\n\n{exc}")

    def _open_edit_dialog(self, order_id: int) -> None:
        dialog = EditOrderDialog(order_id, self)
        if dialog.exec_():
            self.reload_orders()

    def _open_cashier_dialog(self, order_id: int) -> None:
        dialog = FinalizeOrderDialog(order_id, self)
        if dialog.exec_():
            self.reload_orders()
