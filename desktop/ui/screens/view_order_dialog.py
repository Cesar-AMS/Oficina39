from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from services.order_pdf_service import save_order_pdf, suggested_order_pdf_name
from desktop.ui.screens.edit_order_dialog import EditOrderDialog
from desktop.ui.screens.finalize_order_dialog import FinalizeOrderDialog
from desktop.services.order_view_service import load_order_view


def _money(value: float) -> str:
    amount = float(value or 0)
    text = f"{amount:,.2f}"
    return f"R$ {text}".replace(",", "X").replace(".", ",").replace("X", ".")


def _text(value) -> str:
    cleaned = "" if value is None else str(value).strip()
    return cleaned or "---"


class ViewOrderDialog(QDialog):
    def __init__(self, order_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._order_id = order_id
        self.was_updated = False
        self.setWindowTitle(f"Visualizar OS #{order_id}")
        self.resize(980, 760)
        self._content_widget: QWidget | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        self._content_widget = QWidget()
        scroll.setWidget(self._content_widget)
        self._reload_content()
        layout.addWidget(scroll, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        cashier_button = buttons.addButton("Finalizar no Caixa", QDialogButtonBox.ActionRole)
        cashier_button.clicked.connect(self._open_cashier_dialog)
        export_button = buttons.addButton("Exportar PDF", QDialogButtonBox.ActionRole)
        export_button.clicked.connect(self._export_pdf)
        edit_button = buttons.addButton("Editar", QDialogButtonBox.ActionRole)
        edit_button.clicked.connect(self._open_edit_dialog)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        buttons.button(QDialogButtonBox.Close).clicked.connect(self.accept)
        layout.addWidget(buttons)

    def _reload_content(self) -> None:
        if self._content_widget is None:
            return
        data = load_order_view(self._order_id)
        client = data.get("cliente") or {}

        content_layout = QVBoxLayout(self._content_widget)
        while content_layout.count():
            item = content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)

        content_layout.addWidget(self._build_header(data))
        content_layout.addWidget(self._build_identity_section(data, client))
        content_layout.addWidget(self._build_vehicle_section(client))
        content_layout.addWidget(self._build_text_section("Diagnóstico", _text(data.get("diagnostico"))))
        content_layout.addWidget(self._build_text_section("Observações internas", _text(data.get("observacao_interna"))))
        content_layout.addWidget(self._build_services_table(data.get("servicos", [])))
        content_layout.addWidget(self._build_parts_table(data.get("pecas", [])))
        content_layout.addWidget(self._build_financial_section(data))
        content_layout.addWidget(self._build_payments_table(data.get("pagamentos", [])))
        content_layout.addWidget(self._build_attachments_section(data.get("anexos", [])))
        content_layout.addWidget(self._build_timeline_section(data.get("logs_status", [])))
        content_layout.addStretch(1)

    def _open_edit_dialog(self) -> None:
        dialog = EditOrderDialog(self._order_id, self)
        if dialog.exec_():
            self.was_updated = True
            self._reload_content()

    def _open_cashier_dialog(self) -> None:
        dialog = FinalizeOrderDialog(self._order_id, self)
        if dialog.exec_():
            self.was_updated = True
            self._reload_content()

    def _export_pdf(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar PDF da OS",
            suggested_order_pdf_name(self._order_id),
            "Arquivos PDF (*.pdf)",
        )
        if not filename:
            return
        try:
            saved_path = save_order_pdf(self._order_id, filename)
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao exportar", f"Nao foi possivel gerar o PDF.\n\n{exc}")
            return
        QMessageBox.information(self, "PDF exportado", f"Arquivo salvo com sucesso em:\n{saved_path}")

    def _build_header(self, data: dict) -> QWidget:
        card = QFrame()
        card.setObjectName("screenCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(16)

        texts = QVBoxLayout()
        texts.setSpacing(4)

        title = QLabel(f"Ordem de Serviço #{data.get('id')}")
        title.setObjectName("screenTitle")
        subtitle = QLabel(
            f"Status: {_text(data.get('status'))} | Profissional: {_text(data.get('profissional_responsavel'))}"
        )
        subtitle.setObjectName("screenText")
        texts.addWidget(title)
        texts.addWidget(subtitle)

        total = QLabel(_money(data.get("total_cobrado") or data.get("total_geral") or 0))
        total.setObjectName("homeHeroTitle")
        total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addLayout(texts, 1)
        layout.addWidget(total)
        return card

    def _build_identity_section(self, data: dict, client: dict) -> QWidget:
        box = QGroupBox("Dados do cliente")
        layout = QFormLayout(box)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(8)
        layout.addRow("Cliente:", QLabel(_text(client.get("nome_cliente"))))
        layout.addRow("CPF:", QLabel(_text(client.get("cpf"))))
        layout.addRow("Telefone:", QLabel(_text(client.get("telefone"))))
        layout.addRow("E-mail:", QLabel(_text(client.get("email"))))
        layout.addRow("Endereço:", QLabel(_text(client.get("endereco"))))
        layout.addRow("Profissional responsável:", QLabel(_text(data.get("profissional_responsavel"))))
        layout.addRow("Assinatura do cliente:", QLabel(_text(data.get("assinatura_cliente"))))
        return box

    def _build_vehicle_section(self, client: dict) -> QWidget:
        box = QGroupBox("Dados do veículo")
        layout = QFormLayout(box)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(8)
        layout.addRow("Placa:", QLabel(_text(client.get("placa"))))
        layout.addRow("Fabricante:", QLabel(_text(client.get("fabricante"))))
        layout.addRow("Modelo:", QLabel(_text(client.get("modelo"))))
        layout.addRow("Ano:", QLabel(_text(client.get("ano"))))
        layout.addRow("Motor:", QLabel(_text(client.get("motor"))))
        layout.addRow("Combustível:", QLabel(_text(client.get("combustivel"))))
        layout.addRow("Cor:", QLabel(_text(client.get("cor"))))
        layout.addRow("Tanque:", QLabel(_text(client.get("tanque"))))
        layout.addRow("KM:", QLabel(_text(client.get("km"))))
        layout.addRow("Direção:", QLabel(_text(client.get("direcao"))))
        layout.addRow("Ar:", QLabel(_text(client.get("ar"))))
        return box

    def _build_text_section(self, title: str, text: str) -> QWidget:
        box = QGroupBox(title)
        layout = QVBoxLayout(box)
        label = QLabel(text)
        label.setWordWrap(True)
        layout.addWidget(label)
        return box

    def _build_services_table(self, services: list[dict]) -> QWidget:
        box = QGroupBox("Serviços vinculados")
        layout = QVBoxLayout(box)
        table = QTableWidget(max(1, len(services)), 3)
        table.setHorizontalHeaderLabels(["Código", "Descrição", "Valor"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.horizontalHeader().setStretchLastSection(True)

        if services:
            for row, service in enumerate(services):
                table.setItem(row, 0, QTableWidgetItem(_text(service.get("codigo_servico"))))
                table.setItem(row, 1, QTableWidgetItem(_text(service.get("descricao_servico"))))
                item = QTableWidgetItem(_money(service.get("valor_servico") or 0))
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(row, 2, item)
        else:
            table.setItem(0, 0, QTableWidgetItem("Nenhum serviço registrado"))
            table.setSpan(0, 0, 1, 3)

        layout.addWidget(table)
        return box

    def _build_parts_table(self, parts: list[dict]) -> QWidget:
        box = QGroupBox("Peças vinculadas")
        layout = QVBoxLayout(box)
        table = QTableWidget(max(1, len(parts)), 5)
        table.setHorizontalHeaderLabels(["Código", "Descrição", "Qtd", "Valor Unit.", "Total"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)

        if parts:
            for row, part in enumerate(parts):
                quantity = float(part.get("quantidade") or 0)
                unit_value = float(part.get("valor_unitario") or 0)
                total = quantity * unit_value
                table.setItem(row, 0, QTableWidgetItem(_text(part.get("codigo_peca"))))
                table.setItem(row, 1, QTableWidgetItem(_text(part.get("descricao_peca"))))
                quantity_text = str(int(quantity)) if quantity.is_integer() else str(quantity)
                qty_item = QTableWidgetItem(quantity_text)
                qty_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, 2, qty_item)
                unit_item = QTableWidgetItem(_money(unit_value))
                unit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(row, 3, unit_item)
                total_item = QTableWidgetItem(_money(total))
                total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(row, 4, total_item)
        else:
            table.setItem(0, 0, QTableWidgetItem("Nenhuma peça registrada"))
            table.setSpan(0, 0, 1, 5)

        layout.addWidget(table)
        return box

    def _build_financial_section(self, data: dict) -> QWidget:
        box = QGroupBox("Resumo financeiro")
        layout = QFormLayout(box)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(8)
        layout.addRow("Status financeiro:", QLabel(_text(data.get("status_financeiro"))))
        layout.addRow("Forma de pagamento:", QLabel(_text(data.get("forma_pagamento"))))
        layout.addRow("Data de entrada:", QLabel(_text(data.get("data_entrada"))))
        layout.addRow("Data de emissão:", QLabel(_text(data.get("data_emissao"))))
        layout.addRow("Data de retirada:", QLabel(_text(data.get("data_retirada"))))
        layout.addRow("Data de conclusão:", QLabel(_text(data.get("data_conclusao"))))
        layout.addRow("Total serviços:", QLabel(_money(data.get("total_servicos") or 0)))
        layout.addRow("Total peças:", QLabel(_money(data.get("total_pecas") or 0)))
        layout.addRow("Total bruto:", QLabel(_money(data.get("total_geral") or 0)))
        layout.addRow("Desconto:", QLabel(_money(data.get("desconto_valor") or 0)))
        layout.addRow("Total final:", QLabel(_money(data.get("total_cobrado") or 0)))
        layout.addRow("Total pago:", QLabel(_money(data.get("total_pago") or 0)))
        layout.addRow("Saldo pendente:", QLabel(_money(data.get("saldo_pendente") or 0)))
        layout.addRow("Débito vencimento:", QLabel(_text(data.get("debito_vencimento"))))
        layout.addRow("Débito observação:", QLabel(_text(data.get("debito_observacao"))))
        return box

    def _build_payments_table(self, payments: list[dict]) -> QWidget:
        box = QGroupBox("Pagamentos")
        layout = QVBoxLayout(box)
        table = QTableWidget(max(1, len(payments)), 4)
        table.setHorizontalHeaderLabels(["Data", "Forma", "Valor", "Observação"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.horizontalHeader().setStretchLastSection(True)

        if payments:
            for row, payment in enumerate(payments):
                table.setItem(row, 0, QTableWidgetItem(_text(payment.get("data_pagamento"))))
                table.setItem(row, 1, QTableWidgetItem(_text(payment.get("forma_pagamento"))))
                value_item = QTableWidgetItem(_money(payment.get("valor") or 0))
                value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(row, 2, value_item)
                table.setItem(row, 3, QTableWidgetItem(_text(payment.get("observacao"))))
        else:
            table.setItem(0, 0, QTableWidgetItem("Nenhum pagamento registrado"))
            table.setSpan(0, 0, 1, 4)

        layout.addWidget(table)
        return box

    def _build_attachments_section(self, attachments: list[dict]) -> QWidget:
        box = QGroupBox("Anexos")
        layout = QVBoxLayout(box)
        list_widget = QListWidget()
        if attachments:
            for attachment in attachments:
                text = (
                    f"{_text(attachment.get('nome_original'))} | "
                    f"{_text(attachment.get('tipo_mime'))} | "
                    f"{_text(attachment.get('created_at'))}"
                )
                list_widget.addItem(QListWidgetItem(text))
        else:
            list_widget.addItem(QListWidgetItem("Nenhum anexo registrado"))
        layout.addWidget(list_widget)
        return box

    def _build_timeline_section(self, logs: list[dict]) -> QWidget:
        box = QGroupBox("Histórico de status")
        layout = QVBoxLayout(box)
        list_widget = QListWidget()
        if logs:
            for log in logs:
                text = (
                    f"{_text(log.get('data_evento'))} | "
                    f"{_text(log.get('status_anterior'))} -> {_text(log.get('status_novo'))} | "
                    f"Operador: {_text(log.get('operador'))}"
                )
                if log.get("forma_pagamento"):
                    text += f" | Pagamento: {_text(log.get('forma_pagamento'))}"
                if log.get("observacao"):
                    text += f" | Obs: {_text(log.get('observacao'))}"
                list_widget.addItem(QListWidgetItem(text))
        else:
            list_widget.addItem(QListWidgetItem("Nenhum evento de status registrado"))
        layout.addWidget(list_widget)
        return box
