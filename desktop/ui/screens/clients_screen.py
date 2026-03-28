from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop.services.clients_service import find_clients, load_client, remove_client
from desktop.ui.screens.client_form_dialog import ClientFormDialog


def _text(value) -> str:
    cleaned = "" if value is None else str(value).strip()
    return cleaned or "---"


class ClientsScreen(QWidget):
    navigate_requested = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._clients: list[dict] = []
        self._selected_client_id: int | None = None
        self._search_input = QLineEdit()
        self._table = QTableWidget(0, 6)
        self._details_labels: dict[str, QLabel] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(18)

        root.addWidget(self._build_header())
        root.addWidget(self._build_filters_card())
        root.addWidget(self._build_body(), 1)

        self._configure_table()
        self.reload_clients()

    def _build_header(self) -> QWidget:
        card = QFrame()
        card.setObjectName("screenCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        texts = QVBoxLayout()
        title = QLabel("Clientes")
        title.setObjectName("screenTitle")
        subtitle = QLabel(
            "Modulo nativo para listar, cadastrar, editar e excluir clientes usando o banco real do sistema."
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
        layout = QHBoxLayout(card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        self._search_input.setPlaceholderText("Buscar por nome ou CPF")
        self._search_input.returnPressed.connect(self.reload_clients)

        search_button = QPushButton("Buscar")
        search_button.clicked.connect(self.reload_clients)
        clear_button = QPushButton("Limpar")
        clear_button.clicked.connect(self._clear_filters)
        create_button = QPushButton("Novo cliente")
        create_button.clicked.connect(self._open_create_dialog)

        layout.addWidget(self._search_input, 1)
        layout.addWidget(search_button)
        layout.addWidget(clear_button)
        layout.addStretch(1)
        layout.addWidget(create_button)
        return card

    def _build_body(self) -> QWidget:
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._build_table_card())
        splitter.addWidget(self._build_details_card())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setChildrenCollapsible(False)
        return splitter

    def _build_table_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("screenCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.addWidget(self._table)
        return card

    def _build_details_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("screenCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        title = QLabel("Detalhes do cliente")
        title.setObjectName("screenTitle")
        title.setMaximumHeight(36)
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        fields = [
            ("Nome", "nome_cliente"),
            ("CPF", "cpf"),
            ("Telefone", "telefone"),
            ("E-mail", "email"),
            ("Endereco", "endereco"),
            ("Cidade", "cidade"),
            ("Estado", "estado"),
            ("CEP", "cep"),
            ("Placa", "placa"),
            ("Veiculo", "veiculo"),
            ("Motor", "motor"),
            ("Combustivel", "combustivel"),
            ("Cor", "cor"),
            ("KM", "km"),
        ]
        for row, (label, key) in enumerate(fields):
            grid.addWidget(QLabel(f"{label}:"), row, 0)
            value = QLabel("---")
            value.setWordWrap(True)
            self._details_labels[key] = value
            grid.addWidget(value, row, 1)

        layout.addLayout(grid)
        layout.addStretch(1)

        buttons = QHBoxLayout()
        edit_button = QPushButton("Editar")
        edit_button.clicked.connect(self._open_edit_dialog)
        delete_button = QPushButton("Excluir")
        delete_button.clicked.connect(self._delete_selected_client)
        buttons.addWidget(edit_button)
        buttons.addWidget(delete_button)
        layout.addLayout(buttons)
        return card

    def _configure_table(self) -> None:
        self._table.setHorizontalHeaderLabels(["ID", "Cliente", "CPF", "Telefone", "Placa", "Cidade"])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        header = self._table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, header.ResizeToContents)
        header.setSectionResizeMode(1, header.Stretch)
        header.setSectionResizeMode(2, header.ResizeToContents)
        header.setSectionResizeMode(3, header.ResizeToContents)
        header.setSectionResizeMode(4, header.ResizeToContents)
        header.setSectionResizeMode(5, header.Stretch)
        self._table.itemSelectionChanged.connect(self._sync_selected_client)
        self._table.itemDoubleClicked.connect(lambda item: self._open_edit_dialog())

    def _clear_filters(self) -> None:
        self._search_input.clear()
        self.reload_clients()

    def reload_clients(self) -> None:
        try:
            self._clients = find_clients(self._search_input.text().strip())
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar clientes.\n\n{exc}")
            self._clients = []
        self._populate_table()

    def _populate_table(self) -> None:
        self._table.setRowCount(len(self._clients))
        for row, client in enumerate(self._clients):
            values = [
                str(client.get("id") or ""),
                _text(client.get("nome_cliente")),
                _text(client.get("cpf")),
                _text(client.get("telefone")),
                _text(client.get("placa")),
                _text(client.get("cidade")),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 0:
                    item.setData(Qt.UserRole, client.get("id"))
                    item.setTextAlignment(Qt.AlignCenter)
                self._table.setItem(row, col, item)

        if self._clients:
            self._table.selectRow(0)
        else:
            self._selected_client_id = None
            self._apply_client_details({})

    def _get_selected_client_id(self) -> int | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return int(item.data(Qt.UserRole)) if item and item.data(Qt.UserRole) else None

    def _sync_selected_client(self) -> None:
        client_id = self._get_selected_client_id()
        self._selected_client_id = client_id
        if client_id is None:
            self._apply_client_details({})
            return
        try:
            payload = load_client(client_id)
        except Exception as exc:
            QMessageBox.warning(self, "Cliente", f"Nao foi possivel carregar os detalhes.\n\n{exc}")
            self._apply_client_details({})
            return
        self._apply_client_details(payload)

    def _apply_client_details(self, payload: dict) -> None:
        vehicle = " ".join(
            filter(
                None,
                [
                    _text(payload.get("fabricante")) if payload.get("fabricante") else "",
                    _text(payload.get("modelo")) if payload.get("modelo") else "",
                    _text(payload.get("ano")) if payload.get("ano") else "",
                ],
            )
        ).strip()
        mapping = {
            "nome_cliente": payload.get("nome_cliente"),
            "cpf": payload.get("cpf"),
            "telefone": payload.get("telefone"),
            "email": payload.get("email"),
            "endereco": payload.get("endereco"),
            "cidade": payload.get("cidade"),
            "estado": payload.get("estado"),
            "cep": payload.get("cep"),
            "placa": payload.get("placa"),
            "veiculo": vehicle,
            "motor": payload.get("motor"),
            "combustivel": payload.get("combustivel"),
            "cor": payload.get("cor"),
            "km": payload.get("km"),
        }
        for key, label in self._details_labels.items():
            label.setText(_text(mapping.get(key)))

    def _open_create_dialog(self) -> None:
        dialog = ClientFormDialog(parent=self)
        if dialog.exec_():
            self.reload_clients()
            saved_id = int(dialog.saved_client["id"])
            self._select_client_in_table(saved_id)

    def _open_edit_dialog(self) -> None:
        client_id = self._selected_client_id or self._get_selected_client_id()
        if client_id is None:
            QMessageBox.information(self, "Clientes", "Selecione um cliente para editar.")
            return
        dialog = ClientFormDialog(client_id=client_id, parent=self)
        if dialog.exec_():
            self.reload_clients()
            self._select_client_in_table(client_id)

    def _delete_selected_client(self) -> None:
        client_id = self._selected_client_id or self._get_selected_client_id()
        if client_id is None:
            QMessageBox.information(self, "Clientes", "Selecione um cliente para excluir.")
            return
        answer = QMessageBox.question(
            self,
            "Excluir cliente",
            "Deseja realmente excluir o cliente selecionado?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        try:
            remove_client(client_id)
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao excluir", str(exc))
            return

        QMessageBox.information(self, "Sucesso", "Cliente removido com sucesso.")
        self.reload_clients()

    def _select_client_in_table(self, client_id: int) -> None:
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item and item.data(Qt.UserRole) == client_id:
                self._table.selectRow(row)
                self._sync_selected_client()
                break
