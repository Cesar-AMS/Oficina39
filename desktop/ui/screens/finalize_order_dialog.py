from __future__ import annotations

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
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

from desktop.services.order_checkout_service import (
    finalize_order_in_cashier,
    get_checkout_metadata,
    load_checkout_order,
)


def _money(value: float) -> str:
    amount = float(value or 0)
    text = f"{amount:,.2f}"
    return f"R$ {text}".replace(",", "X").replace(".", ",").replace("X", ".")


def _text(value) -> str:
    cleaned = "" if value is None else str(value).strip()
    return cleaned or "---"


def _round_money(value: float) -> float:
    return round(float(value or 0) + 1e-9, 2)


class FinalizeOrderDialog(QDialog):
    def __init__(self, order_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._order_id = order_id
        self._metadata = get_checkout_metadata()
        self._order_data = load_checkout_order(order_id)
        self.saved_order: dict | None = None

        self.setWindowTitle(f"Finalizar no Caixa - OS #{order_id}")
        self.resize(980, 760)

        self._discount_input = QLineEdit()
        self._payment_form_combo = QComboBox()
        self._payment_value_input = QLineEdit()
        self._payment_note_input = QLineEdit()
        self._payments_table = QTableWidget(0, 4)
        self._remove_payment_button: QPushButton | None = None
        self._due_date = QDateEdit()
        self._debit_note_input = QLineEdit()

        self._gross_label = QLabel()
        self._paid_before_label = QLabel()
        self._final_total_label = QLabel()
        self._received_now_label = QLabel()
        self._debit_balance_label = QLabel()
        self._financial_status_label = QLabel()
        self._distributed_label = QLabel("R$ 0,00")
        self._receive_later_label = QLabel("R$ 0,00")
        self._missing_label = QLabel("R$ 0,00")

        self._payment_rows: list[dict] = []

        self._build_ui()
        self._populate_data()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        root.addWidget(self._build_header())
        root.addWidget(self._build_order_card())
        root.addWidget(self._build_payment_card(), 1)
        root.addWidget(self._build_summary_card())

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        save_button = buttons.button(QDialogButtonBox.Save)
        save_button.setText("Concluir recebimento")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self._payments_table.setHorizontalHeaderLabels(["Forma", "Valor", "Observacao", ""])
        self._payments_table.verticalHeader().setVisible(False)
        self._payments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._payments_table.setSelectionMode(QTableWidget.SingleSelection)
        self._payments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        header = self._payments_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, header.ResizeToContents)
        header.setSectionResizeMode(1, header.ResizeToContents)
        header.setSectionResizeMode(2, header.Stretch)
        header.setSectionResizeMode(3, header.ResizeToContents)

    def _build_header(self) -> QWidget:
        card = QFrame()
        card.setObjectName("screenCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        title = QLabel(f"Finalizar no Caixa - OS #{self._order_id}")
        title.setObjectName("screenTitle")
        subtitle = QLabel("Recebimento nativo da OS com desconto, multiplas formas e saldo em debito quando necessario.")
        subtitle.setObjectName("screenText")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        return card

    def _build_order_card(self) -> QWidget:
        box = QGroupBox("Dados da ordem")
        grid = QGridLayout(box)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(8)
        self._order_number_label = QLabel()
        self._client_name_label = QLabel()
        self._phone_label = QLabel()
        self._status_label = QLabel()
        self._payment_form_current_label = QLabel()

        rows = [
            ("OS:", self._order_number_label),
            ("Cliente:", self._client_name_label),
            ("Telefone:", self._phone_label),
            ("Status atual:", self._status_label),
            ("Forma atual:", self._payment_form_current_label),
        ]
        for index, (label, widget) in enumerate(rows):
            grid.addWidget(QLabel(label), index // 2, (index % 2) * 2)
            grid.addWidget(widget, index // 2, (index % 2) * 2 + 1)
        return box

    def _build_payment_card(self) -> QWidget:
        box = QGroupBox("Pagamento")
        layout = QVBoxLayout(box)
        layout.setSpacing(12)

        top = QFormLayout()
        self._discount_input.setPlaceholderText("0,00")
        self._discount_input.editingFinished.connect(self._refresh_summary)
        top.addRow("Desconto (%):", self._discount_input)
        layout.addLayout(top)

        form_row = QHBoxLayout()
        self._payment_form_combo.addItem("Selecione")
        for option in self._metadata.get("formas_pagamento", []):
            self._payment_form_combo.addItem(option)
        self._payment_value_input.setPlaceholderText("0,00")
        self._payment_note_input.setPlaceholderText("Observacao opcional")
        add_button = QPushButton("Adicionar")
        add_button.clicked.connect(self._add_payment_row)
        self._remove_payment_button = QPushButton("Remover selecionada")
        self._remove_payment_button.clicked.connect(self._remove_selected_payment)

        form_row.addWidget(QLabel("Forma"))
        form_row.addWidget(self._payment_form_combo, 1)
        form_row.addWidget(QLabel("Valor"))
        form_row.addWidget(self._payment_value_input)
        form_row.addWidget(QLabel("Observacao"))
        form_row.addWidget(self._payment_note_input, 1)
        form_row.addWidget(add_button)
        form_row.addWidget(self._remove_payment_button)
        layout.addLayout(form_row)
        layout.addWidget(self._payments_table, 1)

        debit_box = QGroupBox("Debito")
        debit_form = QFormLayout(debit_box)
        self._due_date.setCalendarPopup(True)
        self._due_date.setDisplayFormat("dd/MM/yyyy")
        self._due_date.setSpecialValueText("Sem data")
        self._due_date.setDate(QDate.currentDate())
        self._due_date.setEnabled(False)
        self._debit_note_input.setEnabled(False)
        self._due_date.dateChanged.connect(self._refresh_summary)
        self._debit_note_input.textChanged.connect(self._refresh_summary)
        debit_form.addRow("Vencimento:", self._due_date)
        debit_form.addRow("Observacao:", self._debit_note_input)
        layout.addWidget(debit_box)

        footer = QHBoxLayout()
        footer.addWidget(QLabel("Total distribuido:"))
        footer.addWidget(self._distributed_label)
        footer.addSpacing(18)
        footer.addWidget(QLabel("Receber depois:"))
        footer.addWidget(self._receive_later_label)
        footer.addSpacing(18)
        footer.addWidget(QLabel("Falta distribuir:"))
        footer.addWidget(self._missing_label)
        footer.addStretch(1)
        layout.addLayout(footer)
        return box

    def _build_summary_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("screenCard")
        layout = QFormLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(8)
        layout.addRow("Valor bruto:", self._gross_label)
        layout.addRow("Total ja pago:", self._paid_before_label)
        layout.addRow("Valor final da venda:", self._final_total_label)
        layout.addRow("Recebido agora:", self._received_now_label)
        layout.addRow("Saldo para debito:", self._debit_balance_label)
        layout.addRow("Situacao financeira:", self._financial_status_label)
        return card

    def _populate_data(self) -> None:
        client = self._order_data.get("cliente") or {}
        self._order_number_label.setText(f"#{self._order_data.get('id')}")
        self._client_name_label.setText(_text(self._order_data.get("cliente_nome") or client.get("nome_cliente")))
        self._phone_label.setText(_text(client.get("telefone")))
        self._status_label.setText(_text(self._order_data.get("status")))
        self._payment_form_current_label.setText(_text(self._order_data.get("forma_pagamento")))

        discount = float(self._order_data.get("desconto_percentual") or 0)
        self._discount_input.setText(f"{discount:.2f}".replace(".", ",") if discount else "")

        existing_due = self._order_data.get("debito_vencimento")
        if existing_due:
            try:
                day, month, year = existing_due.split("/")
                self._due_date.setDate(QDate(int(year), int(month), int(day)))
            except Exception:
                pass
        self._debit_note_input.setText(self._order_data.get("debito_observacao") or "")
        self._refresh_summary()

    def _parse_money_input(self, value: str) -> float:
        raw = str(value or "").strip().replace("R$", "").replace(".", "").replace(",", ".")
        try:
            return _round_money(float(raw))
        except ValueError:
            return 0.0

    def _current_totals(self) -> dict:
        total_bruto = _round_money(self._order_data.get("total_geral") or 0)
        pago_antes = _round_money(self._order_data.get("total_pago") or 0)
        desconto_percentual = min(100.0, max(0.0, self._parse_money_input(self._discount_input.text())))
        desconto_valor = _round_money(total_bruto * (desconto_percentual / 100.0))
        total_final = _round_money(max(0.0, total_bruto - desconto_valor))
        saldo_base = _round_money(max(0.0, total_final - pago_antes))
        total_formas = _round_money(sum(float(item["valor"]) for item in self._payment_rows))
        total_receber_depois = _round_money(
            sum(float(item["valor"]) for item in self._payment_rows if item["forma_pagamento"].strip().lower() == "receber depois")
        )
        valor_recebido = _round_money(max(0.0, total_formas - total_receber_depois))
        falta_distribuir = _round_money(max(0.0, saldo_base - total_formas))
        saldo_apos = _round_money(max(0.0, total_receber_depois + falta_distribuir))
        return {
            "total_bruto": total_bruto,
            "pago_antes": pago_antes,
            "desconto_percentual": desconto_percentual,
            "desconto_valor": desconto_valor,
            "total_final": total_final,
            "saldo_base": saldo_base,
            "total_formas": total_formas,
            "total_receber_depois": total_receber_depois,
            "valor_recebido": valor_recebido,
            "falta_distribuir": falta_distribuir,
            "saldo_apos": saldo_apos,
        }

    def _financial_status_after(self, saldo_apos: float) -> str:
        if saldo_apos <= 0.009:
            return "Quitado"
        if self._current_totals()["valor_recebido"] > 0:
            return "Parcial"
        return "Pendente"

    def _refresh_summary(self) -> None:
        totals = self._current_totals()
        self._gross_label.setText(_money(totals["total_bruto"]))
        self._paid_before_label.setText(_money(totals["pago_antes"]))
        self._final_total_label.setText(_money(totals["total_final"]))
        self._received_now_label.setText(_money(totals["valor_recebido"]))
        self._debit_balance_label.setText(_money(totals["saldo_apos"]))
        self._financial_status_label.setText(self._financial_status_after(totals["saldo_apos"]))
        self._distributed_label.setText(_money(totals["total_formas"]))
        self._receive_later_label.setText(_money(totals["total_receber_depois"]))
        self._missing_label.setText(_money(totals["falta_distribuir"]))

        enable_debit = totals["saldo_apos"] > 0.009
        self._due_date.setEnabled(enable_debit)
        self._debit_note_input.setEnabled(enable_debit)

    def _render_payments(self) -> None:
        self._payments_table.setRowCount(len(self._payment_rows))
        for row, item in enumerate(self._payment_rows):
            values = [
                item["forma_pagamento"],
                _money(item["valor"]),
                item.get("observacao") or "---",
                "Remover",
            ]
            for col, value in enumerate(values):
                widget_item = QTableWidgetItem(value)
                if col == 1:
                    widget_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if col == 3:
                    widget_item.setTextAlignment(Qt.AlignCenter)
                self._payments_table.setItem(row, col, widget_item)
        self._refresh_summary()

    def _add_payment_row(self) -> None:
        form = self._payment_form_combo.currentText().strip()
        value = self._parse_money_input(self._payment_value_input.text())
        note = self._payment_note_input.text().strip()

        if not form or form == "Selecione":
            QMessageBox.warning(self, "Pagamento", "Selecione a forma de pagamento.")
            return
        if value <= 0:
            QMessageBox.warning(self, "Pagamento", "Informe um valor valido para a forma de pagamento.")
            return

        self._payment_rows.append(
            {
                "forma_pagamento": form,
                "valor": value,
                "observacao": note,
            }
        )
        self._payment_form_combo.setCurrentIndex(0)
        self._payment_value_input.clear()
        self._payment_note_input.clear()
        self._render_payments()

    def _remove_selected_payment(self) -> None:
        row = self._payments_table.currentRow()
        if row < 0 or row >= len(self._payment_rows):
            QMessageBox.information(self, "Pagamento", "Selecione uma forma para remover.")
            return
        self._payment_rows.pop(row)
        self._render_payments()

    def _build_payload(self) -> dict:
        totals = self._current_totals()
        if not self._payment_rows:
            raise ValueError("Adicione pelo menos uma forma de pagamento.")
        if totals["total_formas"] - totals["saldo_base"] > 0.009:
            raise ValueError("A soma das formas nao pode ultrapassar o valor total da venda.")
        if abs(totals["falta_distribuir"]) > 0.009:
            raise ValueError("Distribua todo o valor da venda antes de concluir.")
        if totals["saldo_apos"] > 0.009 and not self._due_date.isEnabled():
            raise ValueError("Informe os dados do debito.")
        if totals["saldo_apos"] > 0.009 and not self._due_date.date().isValid():
            raise ValueError("Informe a data de vencimento do debito.")

        payload = {
            "pagamentos": [
                {
                    "forma_pagamento": item["forma_pagamento"],
                    "valor": item["valor"],
                    "observacao": item.get("observacao") or "",
                }
                for item in self._payment_rows
            ],
            "desconto_percentual": totals["desconto_percentual"],
            "debito_vencimento": self._due_date.date().toString("yyyy-MM-dd") if totals["saldo_apos"] > 0.009 else "",
            "debito_observacao": self._debit_note_input.text().strip() if totals["saldo_apos"] > 0.009 else "",
        }
        return payload

    def _save(self) -> None:
        try:
            payload = self._build_payload()
            self.saved_order = finalize_order_in_cashier(self._order_id, payload)
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao finalizar", str(exc))
            return

        QMessageBox.information(
            self,
            "Recebimento concluido",
            "Finalizacao registrada com sucesso no caixa.",
        )
        self.accept()
