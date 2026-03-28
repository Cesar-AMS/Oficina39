from __future__ import annotations

from typing import Callable

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from desktop.services.clients_service import (
    fetch_address_by_cep,
    fetch_vehicle_by_plate,
    load_client,
    save_client,
)


def _mask_digits(value: str, groups: tuple[int, ...], separators: tuple[str, ...]) -> str:
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    if not digits:
        return ""

    parts = []
    index = 0
    for position, size in enumerate(groups):
        piece = digits[index : index + size]
        if not piece:
            break
        parts.append(piece)
        index += size
        if index >= len(digits):
            break

    result = ""
    for position, part in enumerate(parts):
        result += part
        if position < len(parts) - 1 and position < len(separators):
            result += separators[position]
    return result


def _format_cpf(value: str) -> str:
    return _mask_digits(value, (3, 3, 3, 2), (".", ".", "-"))


def _format_phone(value: str) -> str:
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    if len(digits) <= 10:
        return _mask_digits(digits, (2, 4, 4), (" ", "-"))
    return _mask_digits(digits, (2, 5, 4), (" ", "-"))


def _format_cep(value: str) -> str:
    return _mask_digits(value, (5, 3), ("-",))


def _format_plate(value: str) -> str:
    text = (value or "").strip().upper().replace(" ", "")
    if len(text) >= 7 and "-" not in text and text[:3].isalpha() and text[3:].isalnum():
        return f"{text[:3]}-{text[3:7]}"
    return text


def _text(value) -> str:
    return "" if value is None else str(value).strip()


class ClientFormDialog(QDialog):
    def __init__(self, client_id: int | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._client_id = client_id
        self.saved_client: dict | None = None
        self._fields: dict[str, QLineEdit] = {}

        self.setWindowTitle("Editar cliente" if client_id else "Novo cliente")
        self.resize(860, 760)

        self._build_ui()

        if client_id is not None:
            self._load_existing_client()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel("Cadastro de cliente")
        title.setProperty("role", "title")
        subtitle = QLabel(
            "Preencha os dados do cliente e do veiculo com as mesmas validacoes do dominio atual."
        )
        subtitle.setWordWrap(True)

        root.addWidget(title)
        root.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)
        content_layout.addWidget(self._build_basic_group())
        content_layout.addWidget(self._build_address_group())
        content_layout.addWidget(self._build_vehicle_group())
        content_layout.addStretch(1)

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _build_basic_group(self) -> QWidget:
        box = QGroupBox("Dados do cliente")
        layout = QGridLayout(box)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(10)

        fields = [
            ("Nome", "nome_cliente"),
            ("CPF", "cpf"),
            ("Telefone", "telefone"),
            ("E-mail", "email"),
        ]
        for index, (label, key) in enumerate(fields):
            widget = QLineEdit()
            if key == "cpf":
                widget.editingFinished.connect(lambda key=key: self._apply_formatter(key, _format_cpf))
            elif key == "telefone":
                widget.editingFinished.connect(lambda key=key: self._apply_formatter(key, _format_phone))
            self._fields[key] = widget
            row = index // 2
            col = (index % 2) * 2
            layout.addWidget(QLabel(f"{label}:"), row, col)
            layout.addWidget(widget, row, col + 1)
        return box

    def _build_address_group(self) -> QWidget:
        box = QGroupBox("Endereco")
        outer = QVBoxLayout(box)
        outer.setSpacing(12)

        top = QHBoxLayout()
        cep_field = QLineEdit()
        cep_field.editingFinished.connect(lambda: self._apply_formatter("cep", _format_cep))
        self._fields["cep"] = cep_field
        search_button = QPushButton("Buscar CEP")
        search_button.clicked.connect(self._lookup_cep)
        top.addWidget(QLabel("CEP:"))
        top.addWidget(cep_field, 1)
        top.addWidget(search_button)
        outer.addLayout(top)

        form = QGridLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)
        fields = [
            ("Endereco", "endereco"),
            ("Cidade", "cidade"),
            ("Estado", "estado"),
        ]
        for index, (label, key) in enumerate(fields):
            widget = QLineEdit()
            self._fields[key] = widget
            row = index // 2
            col = (index % 2) * 2
            form.addWidget(QLabel(f"{label}:"), row, col)
            form.addWidget(widget, row, col + 1)
        outer.addLayout(form)
        return box

    def _build_vehicle_group(self) -> QWidget:
        box = QGroupBox("Veiculo")
        outer = QVBoxLayout(box)
        outer.setSpacing(12)

        top = QHBoxLayout()
        plate_field = QLineEdit()
        plate_field.editingFinished.connect(lambda: self._apply_formatter("placa", _format_plate))
        self._fields["placa"] = plate_field
        lookup_button = QPushButton("Consultar placa")
        lookup_button.clicked.connect(self._lookup_plate)
        top.addWidget(QLabel("Placa:"))
        top.addWidget(plate_field, 1)
        top.addWidget(lookup_button)
        outer.addLayout(top)

        form = QGridLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)
        fields = [
            ("Fabricante", "fabricante"),
            ("Modelo", "modelo"),
            ("Ano", "ano"),
            ("Motor", "motor"),
            ("Combustivel", "combustivel"),
            ("Cor", "cor"),
            ("Tanque", "tanque"),
            ("KM", "km"),
            ("Direcao", "direcao"),
            ("Ar", "ar"),
        ]
        for index, (label, key) in enumerate(fields):
            widget = QLineEdit()
            self._fields[key] = widget
            row = index // 2
            col = (index % 2) * 2
            form.addWidget(QLabel(f"{label}:"), row, col)
            form.addWidget(widget, row, col + 1)
        outer.addLayout(form)
        return box

    def _apply_formatter(self, key: str, formatter: Callable[[str], str]) -> None:
        widget = self._fields.get(key)
        if not widget:
            return
        cursor = widget.cursorPosition()
        widget.setText(formatter(widget.text()))
        widget.setCursorPosition(min(cursor, len(widget.text())))

    def _load_existing_client(self) -> None:
        try:
            payload = load_client(int(self._client_id))
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Nao foi possivel carregar o cliente.\n\n{exc}")
            self.reject()
            return

        for key, widget in self._fields.items():
            widget.setText(_text(payload.get(key)))

        self._apply_formatter("cpf", _format_cpf)
        self._apply_formatter("telefone", _format_phone)
        self._apply_formatter("cep", _format_cep)
        self._apply_formatter("placa", _format_plate)

    def _lookup_cep(self) -> None:
        cep = self._fields["cep"].text().strip()
        if not cep:
            QMessageBox.information(self, "CEP", "Informe um CEP antes de consultar.")
            return
        try:
            result = fetch_address_by_cep(cep)
        except Exception as exc:
            QMessageBox.warning(self, "CEP", f"Nao foi possivel consultar o CEP.\n\n{exc}")
            return

        self._fields["endereco"].setText(_text(result.get("logradouro")))
        self._fields["cidade"].setText(_text(result.get("cidade")))
        self._fields["estado"].setText(_text(result.get("estado")).upper()[:2])
        if result.get("cep"):
            self._fields["cep"].setText(_format_cep(str(result.get("cep"))))

    def _lookup_plate(self) -> None:
        plate = self._fields["placa"].text().strip()
        if not plate:
            QMessageBox.information(self, "Placa", "Informe uma placa antes de consultar.")
            return
        try:
            result = fetch_vehicle_by_plate(plate)
        except Exception as exc:
            QMessageBox.warning(self, "Placa", f"Nao foi possivel consultar a placa.\n\n{exc}")
            return

        mapping = {
            "placa": "placa",
            "fabricante": "fabricante",
            "modelo": "modelo",
            "ano": "ano",
            "motor": "motor",
            "combustivel": "combustivel",
            "cor": "cor",
        }
        for source, target in mapping.items():
            if result.get(source):
                self._fields[target].setText(_text(result.get(source)))
        self._apply_formatter("placa", _format_plate)

    def _collect_payload(self) -> dict:
        payload = {key: widget.text().strip() for key, widget in self._fields.items()}
        payload["estado"] = payload.get("estado", "").upper()[:2]
        return payload

    def _save(self) -> None:
        payload = self._collect_payload()
        try:
            self.saved_client = save_client(payload, self._client_id)
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao salvar", str(exc))
            return

        QMessageBox.information(
            self,
            "Sucesso",
            f"Cliente #{self.saved_client['id']} salvo com sucesso.",
        )
        self.accept()
