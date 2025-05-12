# все необходимые импорты
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QFormLayout, QMenuBar,
    QComboBox, QSpinBox, QCheckBox, QListWidget,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QGroupBox, QLabel, QListWidgetItem, QAction
)
from PyQt5.QtCore import Qt, QMargins
import os
import pandas as pd
from sqlalchemy import create_engine, text
import requests

engine = create_engine('sqlite:///DataBase', echo=False)
services = ["PhoneService", "MultipleLines", "InternetService", "OnlineSecurity",
            "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV",
            "StreamingMovies"]
contract_types = ['Month-to-month', 'One year', 'Two year']
payment_types = ['Electronic check', 'Mailed check', 'Bank transfer (automatic)',
                 'Credit card (automatic)']

sup_dict_contact = {
    "Month-to-month": 3875,
    "One year": 1472,
    "Two year": 1685
}
sup_dict_payment = {
    "Electronic check": 2365,
    "Mailed check": 1604,
    "Bank transfer (automatic)": 1542,
    "Credit card (automatic)": 1521
}

# Справочная информация о стоимости услуг
service_prices = {
    "PhoneService": ["≈$13/month", 13],
    "MultipleLines": ["≈$11/month", 11],
    "InternetService": ["≈$13/month", 13],
    "OnlineSecurity": ["≈$11/month", 11],
    "OnlineBackup": ["≈$11/month", 11],
    "DeviceProtection": ["≈$11/month", 11],
    "TechSupport": ["≈$11/month", 11],
    "StreamingTV": ["≈$11/month", 11],
    "StreamingMovies": ["≈$11/month", 11]
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Базовые настройки приложения
        self.setWindowTitle("Churn Prediction App")
        self.setGeometry(100, 100, 1000, 500)

        # Настройка интерфейса
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Создание экранов
        self.main_screen = self.create_main_screen()
        self.history_screen = self.create_history_screen()

        self.stacked_widget.addWidget(self.main_screen)
        self.stacked_widget.addWidget(self.history_screen)

        # Создание меню
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Menu")

        main_action = QAction("Main page", self)
        main_action.triggered.connect(lambda: self.switch_screen(0))
        file_menu.addAction(main_action)

        history_action = QAction("Requests", self)
        history_action.triggered.connect(lambda: self.switch_screen(1))
        file_menu.addAction(history_action)

        exit_action = QAction("Leave from app", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def create_main_screen(self):
        widget = QWidget()
        main_layout = QHBoxLayout()  # Основной горизонтальный layout
        widget.setLayout(main_layout)

        # Левая часть - форма клиента
        form_widget = QWidget()
        form_layout = QVBoxLayout()
        form_widget.setLayout(form_layout)

        # Группировка полей ввода
        form_group = QGroupBox("Customer's form")
        form_layout_inner = QFormLayout()
        form_group.setLayout(form_layout_inner)

        # Поля ввода
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Male", "Female"])

        self.age_spin = QSpinBox()
        self.age_spin.setRange(1, 100)

        self.months_spin = QSpinBox()
        self.months_spin.setRange(0, 60)

        self.partner_check = QCheckBox()
        self.dependent_check = QCheckBox()

        self.services_list = QListWidget()
        self.services_list.addItems(services)
        self.services_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        self.contract_combo = QComboBox()
        self.contract_combo.addItems(contract_types)

        self.paper_check = QCheckBox()

        self.payment_combo = QComboBox()
        self.payment_combo.addItems(payment_types)

        # Добавление полей в форму
        form_layout_inner.addRow(QLabel("Gender:"), self.gender_combo)
        form_layout_inner.addRow(QLabel("Age:"), self.age_spin)
        form_layout_inner.addRow(QLabel("Months in company:"), self.months_spin)
        form_layout_inner.addRow(QLabel("Partner:"), self.partner_check)
        form_layout_inner.addRow(QLabel("Dependents:"), self.dependent_check)
        form_layout_inner.addRow(QLabel("Services:"), self.services_list)
        form_layout_inner.addRow(QLabel("Contract type:"), self.contract_combo)
        form_layout_inner.addRow(QLabel("Paper billing:"), self.paper_check)
        form_layout_inner.addRow(QLabel("Payment method:"), self.payment_combo)

        # Кнопка отправки
        submit_btn = QPushButton("Send a request")
        submit_btn.clicked.connect(self.save_data)

        form_layout.addWidget(form_group)
        form_layout.addWidget(submit_btn)

        # Правая часть - справочная информация
        info_widget = QWidget()
        info_layout = QVBoxLayout()
        info_widget.setLayout(info_layout)

        info_group = QGroupBox("Service Prices")
        info_layout_inner = QVBoxLayout()
        info_group.setLayout(info_layout_inner)

        # Добавляем информацию о стоимости услуг
        info_label = QLabel("Approximate service costs:")
        info_label.setStyleSheet("font-weight: bold;")
        info_layout_inner.addWidget(info_label)

        for service, price in service_prices.items():
            service_label = QLabel(f"{service}: {price[0]}")
            info_layout_inner.addWidget(service_label)

        info_layout.addWidget(info_group)
        info_layout.addStretch()  # Добавляем растягивающееся пространство

        # Добавляем обе части в основной layout
        main_layout.addWidget(form_widget, stretch=2)  # Форма занимает 2/3 пространства
        main_layout.addWidget(info_widget, stretch=1)  # Информация занимает 1/3 пространства

        return widget

    def save_data(self):
        # Получаем список выбранных услуг
        selected_services = [item.text() for item in self.services_list.selectedItems()]

        # Рассчитываем общую стоимость выбранных услуг
        total_cost = 0
        for service in selected_services:
            if service in service_prices:
                total_cost += service_prices[service][1]  # Берем числовое значение стоимости

        # Формируем данные для отправки
        data = {
            "gender": self.gender_combo.currentText(),
            "age": self.age_spin.value(),
            "tenure": self.months_spin.value(),
            "partner": 1 if self.partner_check.isChecked() else 0,
            "dependents": 1 if self.dependent_check.isChecked() else 0,
            "services": selected_services,
            "contract": self.contract_combo.currentText(),
            "paperless_billing": 1 if self.paper_check.isChecked() else 0,
            "payment_method": self.payment_combo.currentText(),
            "monthlyCharges": total_cost  # Добавляем новое поле с общей стоимостью
        }

        try:
            res = requests.post(
                'http://127.0.0.1:8000/save_request/',
                json=data
            )
            res.raise_for_status()  # Проверка на ошибки HTTP

            if res.status_code == 200:
                QMessageBox.information(self, "Success", "Data saved successfully!")
                self.clear_form()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Request failed: {str(e)}")

    def clear_form(self):
        """Очистка формы"""
        self.gender_combo.setCurrentIndex(0)
        self.age_spin.setValue(0)
        self.months_spin.setValue(0)
        self.partner_check.setChecked(False)
        self.dependent_check.setChecked(False)
        self.services_list.clearSelection()
        self.contract_combo.setCurrentIndex(0)
        self.paper_check.setChecked(False)
        self.payment_combo.setCurrentIndex(0)

    def create_history_screen(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Таблица данных
        self.table = QTableWidget()
        self.table.setColumnCount(18)  # Уменьшаем до 18, так как id не отображаем
        self.table.setHorizontalHeaderLabels(["gender", "age", "tenure", "partner",
                                              "dependents", 'PhoneService', 'MultipleLines', 'InternetService',
                                              'OnlineSecurity', 'OnlineBackup', 'DeviceProtection', 'TechSupport',
                                              'StreamingTV', 'StreamingMovies', "Contract", "PaperlessBilling",
                                              "PaymentMethod", "Churn"])

        # Кнопка дообучения
        retrain_btn = QPushButton("Train model")
        retrain_btn.clicked.connect(self.train_model)

        layout.addWidget(self.table)
        layout.addWidget(retrain_btn)

        return widget

    def switch_screen(self, index):
        self.stacked_widget.setCurrentIndex(index)
        if index == 1:
            self.load_history_data()

    def load_history_data(self):
        try:
            # Подключение к базе данных и загрузка данных
            df = pd.read_sql('select * from temp_data', con=engine)

            # Используем индекс как идентификатор записи
            df['record_id'] = df.index

            # Обратное преобразование числовых значений в текстовые
            reverse_contact = {v: k for k, v in sup_dict_contact.items()}
            reverse_payment = {v: k for k, v in sup_dict_payment.items()}

            df['Contract'] = df['adv_Contract'].map(reverse_contact)
            df['PaymentMethod'] = df['adv_paymentMethod'].map(reverse_payment)

            # Установка количества строк и столбцов
            self.table.setRowCount(len(df))
            self.table.setColumnCount(18)  # Теперь 18 колонок без id

            # Установка заголовков (без id)
            headers = ["gender", "age", "tenure", "partner", "dependents",
                       'PhoneService', 'MultipleLines', 'InternetService',
                       'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
                       'TechSupport', 'StreamingTV', 'StreamingMovies',
                       "Contract", "PaperlessBilling", "PaymentMethod", "Churn"]
            self.table.setHorizontalHeaderLabels(headers)

            # Заполнение таблицы данными
            for row_idx, row in df.iterrows():
                for col_idx, col_name in enumerate(headers):
                    if col_name in ['PhoneService', 'MultipleLines', 'InternetService',
                                    'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
                                    'TechSupport', 'StreamingTV', 'StreamingMovies']:
                        # Для услуг используем 1/0
                        value = 1 if row[f'adv_{col_name}'] == 1 else 0
                        item = QTableWidgetItem(str(value))
                    elif col_name == 'Churn':
                        # Для Churn создаем комбобокс
                        combo = QComboBox()
                        combo.addItems(['0', '1'])
                        combo.setCurrentText(str(row['adv_Churn']))
                        combo.currentTextChanged.connect(
                            lambda text, r=row['record_id']: self.update_churn(r, int(text)))
                        self.table.setCellWidget(row_idx, col_idx, combo)
                        continue
                    else:
                        # Для остальных колонок обычный текст
                        value = row[col_name.lower()] if col_name.lower() in df.columns else row.get(col_name, '')
                        item = QTableWidgetItem(str(value))

                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row_idx, col_idx, item)

            # Автоматическое растягивание колонок под содержимое
            self.table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")

    def update_churn(self, record_id, churn):
        try:
            # Обновляем запись в базе данных по индексу
            with engine.connect() as conn:
                conn.execute(
                    text("UPDATE temp_data SET adv_Churn = :churn WHERE rowid = :id"),
                    {'churn': churn, 'id': record_id + 1}  # rowid начинается с 1
                )
                conn.commit()

            QMessageBox.information(self, "Success", "Churn status updated successfully")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update churn: {str(e)}")

    def train_model(self):
        try:
            request = requests.get('http://127.0.0.1:8000/train_model/')

            if request.json() == 1:
                QMessageBox.information(self, "Success", "Model trained successfully!")
            else:
                QMessageBox.warning(self, "Warning", "Model needs more data!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to train model: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
