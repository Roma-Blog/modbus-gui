#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Connection Tab Module
Класс для вкладки подключения в GUI
"""

import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QSpinBox, QComboBox, QTextEdit, QPushButton,
    QRadioButton, QButtonGroup, QCheckBox, QMessageBox, QTabWidget,
    QProgressBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import (
    DEFAULT_COM_PORTS, DEFAULT_BAUDRATES, DEFAULT_CAN_SPEEDS,
    DEFAULT_CAN_ADDRESSES, LIMITS, TEST_MODES, BUTTON_STYLES, AUTO_SEARCH_CONFIG
)


class ConnectionTab(QWidget):
    """Вкладка подключения с элементами управления"""

    def __init__(self, parent=None):
        """
        Инициализация вкладки подключения

        Args:
            parent: Родительский виджет (ModbusRTUGUI)
        """
        super().__init__(parent)
        self.parent = parent
        self.config_manager = None

        # UI элементы
        self.port_combo = None
        self.address_spinbox = None
        self.baudrate_combo = None
        self.can_speed_combo = None
        self.can_address_combo = None
        self.channel1_spinbox = None
        self.channel2_spinbox = None
        self.connect_btn = None
        self.read_config_btn = None
        self.write_config_btn = None
        self.test_group = None
        self.running_lights_radio = None
        self.full_switch_radio = None
        self.snake_radio = None
        self.button_group = None
        self.auto_test_checkbox = None
        self.test_btn = None
        self.auto_search_checkbox = None
        self.search_progress_label = None
        self.search_progress_bar = None

        self.init_ui()

    def init_ui(self):
        """Инициализация пользовательского интерфейса вкладки"""
        layout = QVBoxLayout(self)

        # Контейнер для групп параметров
        params_container = QWidget()
        params_layout = QVBoxLayout(params_container)

        # Первая строка: основные параметры
        row1_layout = QHBoxLayout()
        params_layout.addLayout(row1_layout)

        # Группа параметров соединения (Modbus RTU)
        connection_group = QGroupBox("Параметры соединения (Modbus RTU)")
        connection_layout = QGridLayout(connection_group)

        # Порт
        port_label = QLabel("COM порт:")
        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        self.port_combo.addItems(DEFAULT_COM_PORTS)
        connection_layout.addWidget(port_label, 0, 0)
        connection_layout.addWidget(self.port_combo, 0, 1)

        # Адрес устройства
        address_label = QLabel("Адрес устройства:")
        self.address_spinbox = QSpinBox()
        self.address_spinbox.setRange(LIMITS["MIN_DEVICE_ADDRESS"], LIMITS["MAX_DEVICE_ADDRESS"])
        self.address_spinbox.setValue(4)
        connection_layout.addWidget(address_label, 1, 0)
        connection_layout.addWidget(self.address_spinbox, 1, 1)

        # Скорость
        baudrate_label = QLabel("Скорость (baud):")
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.setEditable(True)
        self.baudrate_combo.addItems(DEFAULT_BAUDRATES)
        self.baudrate_combo.setCurrentText("38400")
        connection_layout.addWidget(baudrate_label, 2, 0)
        connection_layout.addWidget(self.baudrate_combo, 2, 1)

        # Чекбокс автопоиска
        self.auto_search_checkbox = QCheckBox("Автопоиск устройства")
        self.auto_search_checkbox.setToolTip(
            "Автоматический поиск адреса и скорости устройства.\n"
            "Перебор: для каждого адреса тестируются все скорости (115200→9600),\n"
            "затем переход к следующему адресу (1, 2, 3... до 200)."
        )
        self.auto_search_checkbox.setChecked(True)  # По умолчанию включен
        connection_layout.addWidget(self.auto_search_checkbox, 3, 0, 1, 2)

        # Прогресс бар поиска
        self.search_progress_bar = QProgressBar()
        self.search_progress_bar.setVisible(False)
        self.search_progress_bar.setRange(0, 0)  # Непрерывная анимация
        connection_layout.addWidget(self.search_progress_bar, 4, 0, 1, 2)

        # Label статуса поиска
        self.search_progress_label = QLabel("")
        self.search_progress_label.setStyleSheet("QLabel { color: #0066cc; font-style: italic; }")
        self.search_progress_label.setVisible(False)
        connection_layout.addWidget(self.search_progress_label, 5, 0, 1, 2)

        row1_layout.addWidget(connection_group)

        # Группа параметров CAN
        can_group = QGroupBox("Параметры CAN")
        can_layout = QGridLayout(can_group)

        # CAN скорость
        can_speed_label = QLabel("Скорость:")
        self.can_speed_combo = QComboBox()
        self.can_speed_combo.setEditable(True)
        self.can_speed_combo.addItems(DEFAULT_CAN_SPEEDS)
        self.can_speed_combo.setCurrentText("1000K")
        can_layout.addWidget(can_speed_label, 0, 0)
        can_layout.addWidget(self.can_speed_combo, 0, 1)

        # CAN адрес
        can_address_label = QLabel("Адрес:")
        self.can_address_combo = QComboBox()
        self.can_address_combo.setEditable(True)
        self.can_address_combo.addItems(DEFAULT_CAN_ADDRESSES)
        self.can_address_combo.setCurrentText("2")
        can_layout.addWidget(can_address_label, 1, 0)
        can_layout.addWidget(self.can_address_combo, 1, 1)

        row1_layout.addWidget(can_group)

        # Группа конфигурации каналов
        channels_group = QGroupBox("Конфигурация каналов")
        channels_layout = QVBoxLayout(channels_group)

        # Канал 1
        channel1_layout = QHBoxLayout()
        channel1_label = QLabel("Канал 1: кол-во катушек")
        self.channel1_spinbox = QSpinBox()
        self.channel1_spinbox.setRange(0, LIMITS["MAX_COILS_PER_CHANNEL"])
        self.channel1_spinbox.setValue(0)
        channel1_layout.addWidget(channel1_label)
        channel1_layout.addWidget(self.channel1_spinbox)
        channels_layout.addLayout(channel1_layout)

        # Канал 2
        channel2_layout = QHBoxLayout()
        channel2_label = QLabel("Канал 2: кол-во катушек")
        self.channel2_spinbox = QSpinBox()
        self.channel2_spinbox.setRange(0, LIMITS["MAX_COILS_PER_CHANNEL"])
        self.channel2_spinbox.setValue(0)
        channel2_layout.addWidget(channel2_label)
        channel2_layout.addWidget(self.channel2_spinbox)
        channels_layout.addLayout(channel2_layout)

        row1_layout.addWidget(channels_group)

        # Группа управления и операций
        control_group = QGroupBox("Управление")
        control_layout = QVBoxLayout(control_group)

        self.connect_btn = QPushButton("Подключиться")
        self.connect_btn.clicked.connect(self.on_connect_clicked)
        self.connect_btn.setMinimumHeight(35)
        control_layout.addWidget(self.connect_btn)

        self.read_config_btn = QPushButton("Прочитать конфигурацию")
        self.read_config_btn.clicked.connect(self.on_read_config_clicked)
        self.read_config_btn.setEnabled(False)
        self.read_config_btn.setMinimumHeight(35)
        control_layout.addWidget(self.read_config_btn)

        self.write_config_btn = QPushButton("Записать конфигурацию")
        self.write_config_btn.clicked.connect(self.on_write_config_clicked)
        self.write_config_btn.setEnabled(False)
        self.write_config_btn.setMinimumHeight(35)
        control_layout.addWidget(self.write_config_btn)

        row1_layout.addWidget(control_group)

        # Вторая строка: проверка и информация о прошивке
        row2_layout = QHBoxLayout()
        params_layout.addLayout(row2_layout)

        # Группа "Проверка"
        self.test_group = QGroupBox("Проверка")
        test_layout = QVBoxLayout(self.test_group)

        # Радио-кнопки для режимов
        self.running_lights_radio = QRadioButton("Режим бегущие огни")
        self.full_switch_radio = QRadioButton("Режим полного переключения")
        self.snake_radio = QRadioButton("Режим змейка")

        # Группа кнопок
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.running_lights_radio, 0)
        self.button_group.addButton(self.full_switch_radio, 1)
        self.button_group.addButton(self.snake_radio, 2)

        # Обработчики изменения режима
        self.running_lights_radio.clicked.connect(self.on_test_mode_changed)
        self.full_switch_radio.clicked.connect(self.on_test_mode_changed)
        self.snake_radio.clicked.connect(self.on_test_mode_changed)

        # По умолчанию выбрать "Режим полного переключения"
        self.full_switch_radio.setChecked(True)

        test_layout.addWidget(self.running_lights_radio)
        test_layout.addWidget(self.full_switch_radio)
        test_layout.addWidget(self.snake_radio)

        # Чекбокс автоматического тестирования
        self.auto_test_checkbox = QCheckBox("Автоматическое тестирование")
        self.auto_test_checkbox.stateChanged.connect(self.on_auto_test_changed)
        test_layout.addWidget(self.auto_test_checkbox)

        # Кнопка "Тест"
        self.test_btn = QPushButton("Тест")
        self.test_btn.clicked.connect(self.on_test_clicked)
        self.test_btn.setEnabled(False)
        test_layout.addWidget(self.test_btn)

        row2_layout.addWidget(self.test_group)

        # Место для firmware_display (будет добавлено из main)
        self.firmware_layout = row2_layout

        layout.addWidget(params_container)

        # Поле для логов
        self.create_log_area()

    def create_log_area(self):
        """Создание области для логов и дополнительных функций"""
        # Создаем суб-вкладки
        sub_tab_widget = QTabWidget()
        self.layout().addWidget(sub_tab_widget)

        # Суб-вкладка "Логи"
        logs_tab = QWidget()
        logs_layout = QVBoxLayout(logs_tab)
        self.output_text = QTextEdit()
        self.output_text.setFont(QFont("Courier", 10))
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(200)  # Ограниченная высота для логов
        logs_layout.addWidget(self.output_text)
        sub_tab_widget.addTab(logs_tab, "Логи")

        # Суб-вкладка "Дополнительно"
        extra_tab = QWidget()
        extra_layout = QVBoxLayout(extra_tab)
        extra_label = QLabel("Дополнительные функции\nЗдесь можно добавить новые возможности.")
        extra_label.setAlignment(Qt.AlignCenter)
        extra_layout.addWidget(extra_label)
        sub_tab_widget.addTab(extra_tab, "Дополнительно")

    def set_config_manager(self, config_manager):
        """Установить менеджер конфигурации"""
        self.config_manager = config_manager

    def update_connection_buttons(self, port_opened: bool):
        """Обновить состояние кнопок соединения"""
        if port_opened:
            self.connect_btn.setText("Отключиться")
            self.connect_btn.setStyleSheet(BUTTON_STYLES["DISCONNECT"])
            self.read_config_btn.setEnabled(True)
            self.write_config_btn.setEnabled(True)
            self.test_btn.setEnabled(True)
            # Блокируем автопоиск после подключения
            self.auto_search_checkbox.setEnabled(False)
        else:
            self.connect_btn.setText("Подключиться")
            self.connect_btn.setStyleSheet(BUTTON_STYLES["CONNECT"])
            self.read_config_btn.setEnabled(False)
            self.write_config_btn.setEnabled(False)
            self.test_btn.setEnabled(False)
            # Разблокируем автопоиск
            self.auto_search_checkbox.setEnabled(True)

    def set_search_progress(self, visible: bool, status_text: str = ""):
        """
        Управление видимостью элементов прогресса поиска

        Args:
            visible: Показать/скрыть элементы
            status_text: Текст статуса (если visible=True)
        """
        self.search_progress_bar.setVisible(visible)
        self.search_progress_label.setVisible(visible)
        if visible and status_text:
            self.search_progress_label.setText(status_text)
        elif visible:
            self.search_progress_label.setText("Поиск устройства...")

    def is_auto_search_enabled(self) -> bool:
        """Проверить, включен ли автопоиск"""
        return self.auto_search_checkbox.isChecked()

    def update_test_group_state(self, enabled: bool):
        """Обновить состояние группы 'Проверка'"""
        self.test_group.setEnabled(enabled)

    def get_connection_params(self) -> dict:
        """Получить параметры соединения"""
        return {
            "port": self.port_combo.currentText().strip(),
            "address": self.address_spinbox.value(),
            "baudrate": self.baudrate_combo.currentText()
        }

    def get_channel_config(self) -> dict:
        """Получить конфигурацию каналов"""
        return {
            "channel1": self.channel1_spinbox.value(),
            "channel2": self.channel2_spinbox.value()
        }

    def get_modbus_config(self) -> dict:
        """Получить Modbus RTU конфигурацию"""
        return {
            "modbus_speed_text": self.baudrate_combo.currentText(),
            "modbus_address": self.address_spinbox.value()
        }

    def get_can_config(self) -> dict:
        """Получить CAN конфигурацию"""
        return {
            "can_speed_text": self.can_speed_combo.currentText(),
            "can_address": int(self.can_address_combo.currentText()) if self.can_address_combo.currentText().isdigit() else 2
        }

    def get_test_config(self) -> dict:
        """Получить конфигурацию тестирования"""
        mode = TEST_MODES["FULL_SWITCH"]  # по умолчанию
        if self.running_lights_radio.isChecked():
            mode = TEST_MODES["RUNNING_LIGHTS"]
        elif self.full_switch_radio.isChecked():
            mode = TEST_MODES["FULL_SWITCH"]
        elif self.snake_radio.isChecked():
            mode = TEST_MODES["SNAKE"]

        return {
            "mode": mode,
            "auto": self.auto_test_checkbox.isChecked()
        }

    def set_channel_config(self, config: dict):
        """Установить конфигурацию каналов"""
        if "channel1" in config:
            self.channel1_spinbox.setValue(config["channel1"])
        if "channel2" in config:
            self.channel2_spinbox.setValue(config["channel2"])

    def set_modbus_config(self, config: dict):
        """Установить Modbus RTU конфигурацию"""
        if "modbus_speed_text" in config:
            self.baudrate_combo.setCurrentText(config["modbus_speed_text"])
        if "modbus_address" in config:
            self.address_spinbox.setValue(config["modbus_address"])

    def set_can_config(self, config: dict):
        """Установить CAN конфигурацию"""
        if "can_speed_text" in config:
            self.can_speed_combo.setCurrentText(config["can_speed_text"])
        if "can_address" in config:
            self.can_address_combo.setCurrentText(str(config["can_address"]))

    def reset_channel_config(self):
        """Сбросить конфигурацию каналов"""
        self.channel1_spinbox.setValue(0)
        self.channel2_spinbox.setValue(0)

    def add_firmware_display(self, firmware_widget):
        """Добавить виджет информации о прошивке в row2_layout"""
        if hasattr(self, 'firmware_layout'):
            self.firmware_layout.addWidget(firmware_widget)


    # Обработчики событий
    def on_connect_clicked(self):
        """Обработчик нажатия кнопки подключения"""
        if self.parent:
            self.parent.toggle_connection()

    def on_read_config_clicked(self):
        """Обработчик нажатия кнопки чтения конфигурации"""
        if self.parent:
            self.parent.read_device_config()

    def on_write_config_clicked(self):
        """Обработчик нажатия кнопки записи конфигурации"""
        if self.parent:
            self.parent.write_device_config()

    def on_test_mode_changed(self):
        """Обработчик изменения режима тестирования"""
        if self.parent:
            self.parent.on_test_mode_changed()

    def on_auto_test_changed(self, state):
        """Обработчик изменения чекбокса автоматического тестирования"""
        if self.parent:
            self.parent.toggle_auto_testing(state)

    def on_test_clicked(self):
        """Обработчик нажатия кнопки тест"""
        if self.parent:
            self.parent.run_test()
