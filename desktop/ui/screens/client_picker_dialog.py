from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
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

from desktop.services.new_order_service import find_clients


def _text(value) -> str:
    cleaned = "" if value is None else str(value).strip()
    return cleaned or "---"


class ClientPickerDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Selecionar cliente")
        self.resize(860, 520)
        self.selected_client: dict | None = None

        self._search_input = QLineEdit()
        self._table = QTableWidget(0, 6)
        self._clients: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("Busque por nome ou CPF para relacionar um cliente a nova ordem.")
        header.setWordWrap(True)
        layout.addWidget(header)

        filters = QHBoxLayout()
        self._search_input.setPlaceholderText("Digite o nome ou CPF do cliente")
        self._search_input.returnPressed.connect(self._search)
        search_button = QPushButton("Buscar")
        search_button.clicked.connect(self._search)
        filters.addWidget(self._search_input, 1)
        filters.addWidget(search_button)
        layout.addLayout(filters)

        self._table.setHorizontalHeaderLabels(["ID", "Cliente", "CPF", "Telefone", "Veiculo", "Placa"])
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.itemDoubleClicked.connect(self._accept_selected)
        header_view = self._table.horizontalHeader()
        header_view.setStretchLastSection(False)
        header_view.setSectionResizeMode(0, header_view.ResizeToContents)
        header_view.setSectionResizeMode(1, header_view.Stretch)
        header_view.setSectionResizeMode(2, header_view.ResizeToContents)
        header_view.setSectionResizeMode(3, header_view.ResizeToContents)
        header_view.setSectionResizeMode(4, header_view.Stretch)
        header_view.setSectionResizeMode(5, header_view.ResizeToContents)
        layout.addWidget(self._table, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept_selected)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _search(self) -> None:
        term = self._search_input.text().strip()
        if len(term) < 2:
            QMessageBox.information(self, "Busca", "Digite pelo menos 2 caracteres para buscar clientes.")
            return

        try:
            self._clients = find_clients(term)
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao buscar clientes.\n\n{exc}")
            self._clients = []
        self._populate_table()

    def _populate_table(self) -> None:
        self._table.setRowCount(len(self._clients))
        for row, client in enumerate(self._clients):
            vehicle = " ".join(filter(None, [(client.get("fabricante") or "").strip(), (client.get("modelo") or "").strip()])) or "---"
            values = [
                str(client.get("id") or ""),
                _text(client.get("nome_cliente")),
                _text(client.get("cpf")),
                _text(client.get("telefone")),
                vehicle,
                _text(client.get("placa")),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col in {0, 2, 3, 5}:
                    item.setTextAlignment(Qt.AlignCenter)
                if col == 0:
                    item.setData(Qt.UserRole, client)
                self._table.setItem(row, col, item)

    def _accept_selected(self, *args) -> None:
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Cliente", "Selecione um cliente para continuar.")
            return
        item = self._table.item(row, 0)
        self.selected_client = item.data(Qt.UserRole) if item else None
        if not self.selected_client:
            QMessageBox.warning(self, "Cliente", "Nao foi possivel identificar o cliente selecionado.")
            return
        self.accept()
