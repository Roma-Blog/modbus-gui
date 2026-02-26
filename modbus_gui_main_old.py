#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modbus GUI Main Module
Модуль для главного окна GUI приложения Modbus RTU Scanner
"""

import sys
import os
from datetime import datetime

# PyQt5 импорты
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QGroupBox, QLabel, QSpinBox, QComboBox,
    QTextEdit, QPushButton, QProgressBar, QStatusBar, QMessageBox,
    QTabWidget, QRadioButton, QButtonGroup, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer, QThread
from PyQt5.QtGui import QFont

# Добавляем путь для импорта наших модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
shared_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'shared')
sys.path.insert(0, shared_path)

from modbus_worker import ModbusWorkerThread

class ModbusRTUGUI(QMainWindow):
    """Главное окно приложения Modbus RTU"""

    def __init__(self):
        super().__init__()
        self.worker_thread = None
        self.device_data = {}
        self.connection_status = False

        # Атрибуты для группы "Проверка"
        self.test_mode = "full_switch"  # режим по умолчанию
        self.auto_test = False
        self.config_read = False  # флаг, прочитана ли конфигурация
        self.auto_testing_active = False  # флаг активного автоматического тестирования
        self.full_switch_state = False  # состояние для режима полного переключения (False = все выключено, True = все включено)
        self.snake_active = False  # флаг активного snake теста
        self.snake_step = 0  # текущий шаг snake теста
        self.is_scanning = False  # флаг активного сканирования адресов
        self.port_opened = False  # флаг, открыт ли порт

        self.init_ui()
        self.setup_timers()

        # Сканируем доступные COM порты и заполняем список
        self._scan_available_ports()

        # Логируем запуск приложения
        print("[GUI] Modbus RTU Scanner GUI запущен")
        print("[GUI] Для подключения к устройству используйте вкладку 'Подключение'")
        print("[GUI] ВАЖНО: Убедитесь, что выбрали правильный COM порт!")
        print("[GUI] Проверьте в Диспетчере устройств Windows, какой COM порт назначен вашему устройству")
        self.log_message("Приложение запущено. Выберите правильный COM порт и нажмите 'Подключиться'")
        self.log_message("Если подключение не удается, проверьте: порт, скорость, адрес устройства")

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle("Modbus RTU Scanner GUI")
        self.setGeometry(100, 100, 1200, 800)

        # Создаем постоянные labels для status bar
        self.connection_info_label = QLabel("Соединение не установлено")
        self.connection_info_label.setStyleSheet("QLabel { font-weight: bold; color: red; }")
        self.last_read_label = QLabel("Последнее чтение: -")

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        self.main_layout = QVBoxLayout(central_widget)

        # Создаем вкладки
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        # Создаем вкладки интерфейса
        self.create_connection_tab()

        # Поле для логов
        self.create_log_area()

        # Строка состояния
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")

        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # Добавляем постоянные виджеты в status bar
        self.status_bar.addPermanentWidget(self.connection_info_label)
        self.status_bar.addPermanentWidget(self.last_read_label)



    def create_connection_tab(self):
        """Создание вкладки подключения"""
        connection_widget = QWidget()
        layout = QVBoxLayout(connection_widget)

        # Контейнер для групп параметров (Modbus RTU и CAN)
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
        self.port_combo.addItems(["COM1", "COM2", "COM3", "COM4", "COM5", "/dev/ttyUSB0", "/dev/ttyUSB1"])
        connection_layout.addWidget(port_label, 0, 0)
        connection_layout.addWidget(self.port_combo, 0, 1)

        # Адрес устройства
        address_label = QLabel("Адрес устройства:")
        self.address_spinbox = QSpinBox()
        self.address_spinbox.setRange(1, 247)
        self.address_spinbox.setValue(4)
        connection_layout.addWidget(address_label, 1, 0)
        connection_layout.addWidget(self.address_spinbox, 1, 1)

        # Скорость
        baudrate_label = QLabel("Скорость (baud):")
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.setEditable(True)
        self.baudrate_combo.addItems(["Автоопределение", "9600", "19200", "38400", "57600", "115200"])
        self.baudrate_combo.setCurrentText("38400")
        connection_layout.addWidget(baudrate_label, 2, 0)
        connection_layout.addWidget(self.baudrate_combo, 2, 1)

        row1_layout.addWidget(connection_group)

        # Группа параметров CAN
        can_group = QGroupBox("Параметры CAN")
        can_layout = QGridLayout(can_group)

        # CAN скорость
        can_speed_label = QLabel("Скорость:")
        self.can_speed_combo = QComboBox()
        self.can_speed_combo.setEditable(True)
        self.can_speed_combo.addItems(["100K", "125K", "250K", "500K", "1000K"])
        self.can_speed_combo.setCurrentText("1000K")
        can_layout.addWidget(can_speed_label, 0, 0)
        can_layout.addWidget(self.can_speed_combo, 0, 1)

        # CAN адрес
        can_address_label = QLabel("Адрес:")
        self.can_address_combo = QComboBox()
        self.can_address_combo.setEditable(True)
        self.can_address_combo.addItems(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])
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
        self.channel1_spinbox.setRange(0, 65535)
        self.channel1_spinbox.setValue(0)
        channel1_layout.addWidget(channel1_label)
        channel1_layout.addWidget(self.channel1_spinbox)
        channels_layout.addLayout(channel1_layout)

        # Канал 2
        channel2_layout = QHBoxLayout()
        channel2_label = QLabel("Канал 2: кол-во катушек")
        self.channel2_spinbox = QSpinBox()
        self.channel2_spinbox.setRange(0, 65535)
        self.channel2_spinbox.setValue(0)
        channel2_layout.addWidget(channel2_label)
        channel2_layout.addWidget(self.channel2_spinbox)
        channels_layout.addLayout(channel2_layout)

        row1_layout.addWidget(channels_group)

        # Группа управления и операций
        control_group = QGroupBox("Управление")
        control_layout = QVBoxLayout(control_group)

        self.connect_btn = QPushButton("Подключиться")
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.connect_btn.setMinimumHeight(35)
        control_layout.addWidget(self.connect_btn)

        self.read_config_btn = QPushButton("Прочитать конфигурацию")
        self.read_config_btn.clicked.connect(self.read_device_config)
        self.read_config_btn.setEnabled(False)
        self.read_config_btn.setMinimumHeight(35)
        control_layout.addWidget(self.read_config_btn)

        self.write_config_btn = QPushButton("Записать конфигурацию")
        self.write_config_btn.clicked.connect(self.write_device_config)
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
        self.auto_test_checkbox.stateChanged.connect(self.toggle_auto_testing)
        test_layout.addWidget(self.auto_test_checkbox)

        # Кнопка "Тест"
        self.test_btn = QPushButton("Тест")
        self.test_btn.clicked.connect(self.run_test)
        self.test_btn.setEnabled(False)
        test_layout.addWidget(self.test_btn)

        row2_layout.addWidget(self.test_group)

        # Информация о прошивке
        firmware_group = QGroupBox("Информация о прошивке")
        firmware_layout = QVBoxLayout(firmware_group)

        self.firmware_text = QTextEdit()
        self.firmware_text.setFont(QFont("Courier", 10))
        self.firmware_text.setReadOnly(True)
        self.firmware_text.setMaximumHeight(200)  # Ограниченная высота для информации о прошивке
        firmware_layout.addWidget(self.firmware_text)

        row2_layout.addWidget(firmware_group)

        layout.addWidget(params_container)

        # Добавляем вкладку
        self.tab_widget.addTab(connection_widget, "Подключение")







    def create_log_area(self):
        """Создание области для логов"""
        # Группа логов
        log_group = QGroupBox("Логи")
        self.main_layout.addWidget(log_group)

        log_layout = QVBoxLayout(log_group)

        self.output_text = QTextEdit()
        self.output_text.setFont(QFont("Courier", 10))
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(200)  # Ограниченная высота для логов
        log_layout.addWidget(self.output_text)

    def setup_timers(self):
        """Настройка таймеров"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.setInterval(2000)  # 2 секунды
        self.update_timer.start()

        # Таймер для автоматического тестирования
        self.auto_test_timer = QTimer()
        self.auto_test_timer.timeout.connect(self.run_auto_test_cycle)
        self.auto_test_timer.setInterval(500)  # 0.5 секунды

    def toggle_connection(self):
        """Переключение состояния соединения"""
        if not self.port_opened:
            self.connect()
        else:
            self.disconnect_connection()

    def connect(self):
        """Подключение к устройству через Modbus RTU"""
        port = self.port_combo.currentText().strip()
        address = self.address_spinbox.value()
        baudrate_text = self.baudrate_combo.currentText()

        if not port:
            QMessageBox.warning(self, "Ошибка", "Выберите COM порт")
            return

        # Проверяем доступность порта
        if not self._is_port_available(port):
            QMessageBox.warning(self, "Ошибка", f"Порт {port} недоступен")
            return

        # Устанавливаем флаг, что порт открыт
        self.port_opened = True
        self.update_connection_buttons()

        # Показываем прогресс
        self.progress_bar.setVisible(True)
        self.status_bar.showMessage("Подключение к устройству...")

        # Определяем скорость
        if baudrate_text == "Автоопределение":
            baudrate = 9600  # Начнем с 9600 для поиска
        else:
            baudrate = int(baudrate_text)

        self.log_message(f"Попытка подключения: порт {port}, адрес {address}, скорость {baudrate}")

        # Создаем worker_thread для подключения
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.worker_thread.wait()

        self.worker_thread = ModbusWorkerThread(port, address, baudrate)
        self.worker_thread.connected.connect(self.on_connected)
        self.worker_thread.error_occurred.connect(self.on_error_occurred)
        self.worker_thread.status_updated.connect(self.on_status_updated)
        self.worker_thread.start()

        # Ждем немного для инициализации
        QTimer.singleShot(2000, self._check_connection_timeout)

    def _check_connection_timeout(self):
        """Проверить таймаут подключения и запустить поиск адреса при необходимости"""
        if not self.connection_status and self.worker_thread:
            # Подключение не удалось - пытаемся найти устройство на других адресах
            port = self.port_combo.currentText().strip()
            baudrate_text = self.baudrate_combo.currentText()

            if baudrate_text == "Автоопределение":
                self.log_message("[INFO] Автоопределение скорости не поддерживается при подключении - выберите фиксированную скорость")
                self.progress_bar.setVisible(False)
                self.connection_info_label.setText("Ошибка: выберите фиксированную скорость")
                self.connection_info_label.setStyleSheet("QLabel { font-weight: bold; color: red; }")
                self.status_bar.showMessage("Ошибка подключения")
                self.port_opened = False
                self.update_connection_buttons()
                return

            baudrate = int(baudrate_text)
            self.log_message(f"[INFO] Устройство не отвечает на адрес {self.address_spinbox.value()}, запускаем поиск адреса...")

            # Запускаем поиск адреса
            device_info, found_address = self.worker_thread.auto_detect_address_with_command17(port, baudrate)

            if device_info and found_address:
                # Устройство найдено - обновляем GUI и подключаемся
                self.address_spinbox.setValue(found_address)
                self.display_firmware_info(device_info, baudrate)

                # Читаем конфигурацию каналов
                self.read_channel_config()

                # Автоматически читаем Modbus RTU параметры
                self.read_modbus_rtu_config_from_device(self.worker_thread)

                self.on_connected(True, f"Устройство найдено на адресе {found_address}")
            else:
                # Устройство не найдено
                self.on_connected(False, "Устройство не найдено на доступных адресах")



    def read_modbus_rtu_config_from_device(self, worker_thread):
        """Прочитать Modbus RTU параметры (регистры 3 и 6) и обновить GUI"""
        try:
            # Читаем регистр 3 (скорость Modbus)
            speed_data = worker_thread.read_holding_registers(3, 1)
            # Читаем регистр 6 (адрес Modbus)
            address_data = worker_thread.read_holding_registers(6, 1)

            if speed_data and "holding_registers" in speed_data and len(speed_data["holding_registers"]) >= 1:
                speed_value = speed_data["holding_registers"][0]
                speed_text = self._modbus_speed_value_to_text(speed_value)
                self.baudrate_combo.setCurrentText(speed_text)
                self.log_message(f"Прочитана скорость Modbus: {speed_text}")

            if address_data and "holding_registers" in address_data and len(address_data["holding_registers"]) >= 1:
                address_value = address_data["holding_registers"][0]
                if 1 <= address_value <= 247:
                    self.address_spinbox.setValue(address_value)
                    self.log_message(f"Прочитан адрес Modbus: {address_value}")

        except Exception as e:
            self.log_message(f"Ошибка чтения Modbus RTU параметров: {str(e)}")

    def disconnect_device(self):
        """Отключение от устройства"""
        if self.worker_thread:
            self.worker_thread.stop()
            self.worker_thread.wait()
            self.worker_thread = None

        self.connection_status = False
        self.config_read = False  # сбрасываем флаг чтения конфигурации
        self.stop_auto_testing()  # останавливаем автоматическое тестирование
        self.update_connection_buttons()

        # Сбрасываем поля каналов при отключении
        self.channel1_spinbox.setValue(0)
        self.channel2_spinbox.setValue(0)

        self.status_bar.showMessage("Отключено")
        self.log_message("Соединение с устройством отключено пользователем")

    def on_connected(self, success: bool, message: str):
        """Обработка результата подключения"""
        self.progress_bar.setVisible(False)

        if success:
            self.connection_status = True
            self.connection_info_label.setText(message)
            self.connection_info_label.setStyleSheet("QLabel { font-weight: bold; color: green; }")
            self.status_bar.showMessage("Подключено")
            self.log_message(f"[OK] {message}")

            # Активируем кнопки операций
            self.update_connection_buttons()

            # Автоматически читаем конфигурацию при успешном подключении
            if "найдено на адресе" in message.lower():
                # Устройство найдено через поиск адреса - читаем конфигурацию
                self.read_channel_config()
                self.config_read = True
                self.update_test_group_state()
        else:
            self.connection_status = False
            self.connection_info_label.setText(message)
            self.connection_info_label.setStyleSheet("QLabel { font-weight: bold; color: red; }")
            self.status_bar.showMessage("Ошибка подключения")
            self.log_message(f"[FAIL] {message}")
            self.update_connection_buttons()

    def on_error_occurred(self, error_message: str):
        """Обработка ошибок"""
        self.log_message(f"Ошибка: {error_message}")
        if not self.connection_status:
            self.progress_bar.setVisible(False)
            self.update_connection_buttons()

    def on_status_updated(self, status_message: str):
        """Обработка обновлений статуса"""
        self.log_message(f"[STATUS] {status_message}")
        self.status_bar.showMessage(status_message)

    def update_connection_buttons(self):
        """Обновление состояния кнопок соединения и операций"""
        if self.port_opened:
            # Порт открыт - показываем кнопку отключения
            self.connect_btn.setText("Отключиться")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
                QPushButton:pressed {
                    background-color: #bd2130;
                }
            """)
            # Включаем кнопки операций
            self.read_config_btn.setEnabled(True)
            self.write_config_btn.setEnabled(True)
            self.test_btn.setEnabled(True)
        else:
            # Порт закрыт - показываем кнопку подключения
            self.connect_btn.setText("Подключиться")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
                QPushButton:pressed {
                    background-color: #1e7e34;
                }
            """)
            # Отключаем кнопки операций
            self.read_config_btn.setEnabled(False)
            self.write_config_btn.setEnabled(False)
            self.test_btn.setEnabled(False)

        self.connect_btn.setEnabled(True)
        self.update_test_group_state()

    def update_test_group_state(self):
        """Обновление состояния группы 'Проверка'"""
        # Группа доступна только если подключено и прочитана конфигурация
        enabled = self.connection_status and self.config_read
        self.test_group.setEnabled(enabled)

    def disconnect_connection(self):
        """Отключение от устройства и закрытие порта"""
        self.disconnect_device()
        # Сбрасываем флаг открытия порта
        self.port_opened = False

    def run_test(self):
        """Запуск тестирования устройства"""
        if not self.connection_status or not self.worker_thread:
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к устройству")
            return

        # Определяем выбранный режим
        mode = ""
        if self.running_lights_radio.isChecked():
            mode = "running_lights"
        elif self.full_switch_radio.isChecked():
            mode = "full_switch"
        elif self.snake_radio.isChecked():
            mode = "snake"

        # Проверяем чекбокс автоматического тестирования
        auto = self.auto_test_checkbox.isChecked()

        # Если автоматическое тестирование уже активно - остановить его и выполнить один цикл
        if self.auto_testing_active:
            self.log_message(f"[TEST] Остановка автоматического тестирования и выполнение одного цикла режима '{mode}'")
            self.stop_auto_testing()

            # Выполняем один шаг в зависимости от режима
            if mode == "running_lights":
                self.running_lights_next_step()
            elif mode == "full_switch":
                self.run_full_switch_test()
            elif mode == "snake":
                self.snake_next_step()
        else:
            # Обычная логика запуска
            self.log_message(f"Запуск теста: режим '{mode}', автоматическое тестирование: {auto}")

            # Выполняем тест в зависимости от режима
            if mode == "running_lights":
                self.run_running_lights_test()
            elif mode == "full_switch":
                self.run_full_switch_test()
            elif mode == "snake":
                self.run_snake_test()

            # Если автоматическое тестирование включено, запускаем таймер
            if auto and not self.auto_testing_active:
                self.start_auto_testing()

    def run_running_lights_test(self):
        """Тестирование режима бегущих огней (бегущий огонь с 3 активными катушками)"""
        self.log_message("[TEST] Выполнение теста: Режим бегущие огни")

        if not self.connection_status or not self.worker_thread:
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к устройству")
            return

        # Получаем значения каналов
        channel1_value = self.channel1_spinbox.value()
        channel2_value = self.channel2_spinbox.value()

        self.log_message(f"[TEST] Канал 1: {channel1_value} катушек (coils 0-{channel1_value-1})")
        self.log_message(f"[TEST] Канал 2: {channel2_value} катушек (coils 32-{32+channel2_value-1})")

        # Проверяем минимальные значения
        if channel1_value < 3:
            QMessageBox.warning(self, "Ошибка", "Канал 1 должен иметь минимум 3 катушки")
            return
        if channel2_value < 3:
            QMessageBox.warning(self, "Ошибка", "Канал 2 должен иметь минимум 3 катушки")
            return

        # Запускаем тест в отдельном потоке или с таймером
        self.running_lights_active = True
        self.running_lights_step = 0

        # Создаем таймер для последовательного выполнения шагов
        if hasattr(self, 'running_lights_timer'):
            self.running_lights_timer.stop()
        self.running_lights_timer = QTimer()
        self.running_lights_timer.timeout.connect(self.running_lights_next_step)
        self.running_lights_timer.setInterval(500)  # 0.5 секунды между шагами
        self.running_lights_timer.start()

        self.log_message("[TEST] Запуск бегущего огня...")

    def running_lights_next_step(self):
        """Выполнить следующий шаг бегущего огня"""
        if not self.running_lights_active:
            return

        channel1_value = self.channel1_spinbox.value()
        channel2_value = self.channel2_spinbox.value()

        # Количество шагов для каждого канала
        max_steps_channel1 = channel1_value - 2
        max_steps_channel2 = channel2_value - 2

        # Определяем текущий шаг для каждого канала
        step1 = self.running_lights_step % max_steps_channel1
        step2 = self.running_lights_step % max_steps_channel2

        # Канал 1: coils 0 to channel1_value-1
        # Всегда 3 активных: step1, step1+1, step1+2
        channel1_coils = [False] * channel1_value
        if step1 < max_steps_channel1:
            channel1_coils[step1] = True
            channel1_coils[step1 + 1] = True
            channel1_coils[step1 + 2] = True

        # Канал 2: coils 32 to 32+channel2_value-1
        # Всегда 3 активных: step2, step2+1, step2+2
        channel2_coils = [False] * channel2_value
        if step2 < max_steps_channel2:
            channel2_coils[step2] = True
            channel2_coils[step2 + 1] = True
            channel2_coils[step2 + 2] = True

        # Отправляем coils для канала 1
        if channel1_coils and self.worker_thread:
            result1 = self.worker_thread.write_coils(0, channel1_coils)
            if result1 and result1.get("status") == "success":
                active_coils1 = [i for i, v in enumerate(channel1_coils) if v]
                self.log_message(f"[TEST] Канал 1: активные coils {active_coils1}")
            else:
                self.log_message("[TEST] Ошибка записи coils для Канала 1")

        # Отправляем coils для канала 2
        if channel2_coils and self.worker_thread:
            result2 = self.worker_thread.write_coils(32, channel2_coils)
            if result2 and result2.get("status") == "success":
                active_coils2 = [32 + i for i, v in enumerate(channel2_coils) if v]
                self.log_message(f"[TEST] Канал 2: активные coils {active_coils2}")
            else:
                self.log_message("[TEST] Ошибка записи coils для Канала 2")

        # Увеличиваем шаг
        self.running_lights_step += 1

        # Проверяем, нужно ли остановить тест (после нескольких циклов)
        if self.running_lights_step >= max(max_steps_channel1, max_steps_channel2) * 3:  # 3 цикла
            self.stop_running_lights_test()

    def stop_running_lights_test(self):
        """Остановить тест бегущих огней"""
        self.running_lights_active = False
        if hasattr(self, 'running_lights_timer'):
            self.running_lights_timer.stop()
            delattr(self, 'running_lights_timer')

        # Выключаем все coils
        channel1_value = self.channel1_spinbox.value()
        channel2_value = self.channel2_spinbox.value()

        if channel1_value > 0 and self.worker_thread:
            self.worker_thread.write_coils(0, [False] * channel1_value)
        if channel2_value > 0 and self.worker_thread:
            self.worker_thread.write_coils(32, [False] * channel2_value)

        self.log_message("[TEST] Тест бегущих огней завершен")

    def run_full_switch_test(self):
        """Тестирование режима полного переключения (все coils ON/OFF по нажатию)"""
        self.log_message("[TEST] Выполнение теста: Режим полного переключения")

        if not self.connection_status or not self.worker_thread:
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к устройству")
            return

        # Получаем значения каналов
        channel1_value = self.channel1_spinbox.value()
        channel2_value = self.channel2_spinbox.value()

        self.log_message(f"[TEST] Канал 1: {channel1_value} катушек (coils 0-{channel1_value-1})")
        self.log_message(f"[TEST] Канал 2: {channel2_value} катушек (coils 32-{32+channel2_value-1})")

        # Переключаем состояние
        if self.full_switch_state:
            # Были включены - выключаем все
            new_state = False
            self.full_switch_state = False
            self.log_message("[TEST] Выключение всех coils")
        else:
            # Были выключены - включаем все
            new_state = True
            self.full_switch_state = True
            self.log_message("[TEST] Включение всех coils")

        # Создаем списки значений для coils
        channel1_coils = [new_state] * channel1_value if channel1_value > 0 else []
        channel2_coils = [new_state] * channel2_value if channel2_value > 0 else []

        # Отправляем coils для канала 1
        if channel1_coils:
            result1 = self.worker_thread.write_coils(0, channel1_coils)
            if result1 and result1.get("status") == "success":
                state_text = "ON" if new_state else "OFF"
                self.log_message(f"[TEST] Канал 1: все coils установлены в {state_text}")
            else:
                self.log_message("[TEST] Ошибка записи coils для Канала 1")

        # Отправляем coils для канала 2
        if channel2_coils:
            result2 = self.worker_thread.write_coils(32, channel2_coils)
            if result2 and result2.get("status") == "success":
                state_text = "ON" if new_state else "OFF"
                self.log_message(f"[TEST] Канал 2: все coils установлены в {state_text}")
            else:
                self.log_message("[TEST] Ошибка записи coils для Канала 2")

        self.log_message(f"[TEST] Текущее состояние: {'ВКЛЮЧЕНО' if self.full_switch_state else 'ВЫКЛЮЧЕНО'}")

    def run_snake_test(self):
        """Тестирование режима змейка (последовательное включение всех coils)"""
        self.log_message("[TEST] Выполнение теста: Режим змейка")

        if not self.connection_status or not self.worker_thread:
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к устройству")
            return

        # Получаем значения каналов
        channel1_value = self.channel1_spinbox.value()
        channel2_value = self.channel2_spinbox.value()

        self.log_message(f"[TEST] Канал 1: {channel1_value} катушек (coils 0-{channel1_value-1})")
        self.log_message(f"[TEST] Канал 2: {channel2_value} катушек (coils 32-{32+channel2_value-1})")

        # Проверяем минимальные значения
        if channel1_value < 1:
            QMessageBox.warning(self, "Ошибка", "Канал 1 должен иметь минимум 1 катушку")
            return
        if channel2_value < 1:
            QMessageBox.warning(self, "Ошибка", "Канал 2 должен иметь минимум 1 катушку")
            return

        # Запускаем тест
        self.snake_active = True
        self.snake_step = 0

        # Создаем таймер для последовательного включения
        if hasattr(self, 'snake_timer'):
            self.snake_timer.stop()
        self.snake_timer = QTimer()
        self.snake_timer.timeout.connect(self.snake_next_step)
        self.snake_timer.setInterval(500)  # 0.5 секунды между шагами
        self.snake_timer.start()

        self.log_message("[TEST] Запуск змейки...")

    def snake_next_step(self):
        """Выполнить следующий шаг змейки"""
        if not self.snake_active:
            return

        channel1_value = self.channel1_spinbox.value()
        channel2_value = self.channel2_spinbox.value()

        # Создаем списки coils для текущего шага
        # Включаем coils от 0 до snake_step
        channel1_coils = [i <= self.snake_step for i in range(channel1_value)]
        channel2_coils = [i <= self.snake_step for i in range(channel2_value)]

        # Отправляем coils для канала 1
        if channel1_coils and self.worker_thread:
            result1 = self.worker_thread.write_coils(0, channel1_coils)
            if result1 and result1.get("status") == "success":
                active_coils1 = [i for i, v in enumerate(channel1_coils) if v]
                self.log_message(f"[TEST] Канал 1: активные coils {active_coils1}")
            else:
                self.log_message("[TEST] Ошибка записи coils для Канала 1")

        # Отправляем coils для канала 2
        if channel2_coils and self.worker_thread:
            result2 = self.worker_thread.write_coils(32, channel2_coils)
            if result2 and result2.get("status") == "success":
                active_coils2 = [32 + i for i, v in enumerate(channel2_coils) if v]
                self.log_message(f"[TEST] Канал 2: активные coils {active_coils2}")
            else:
                self.log_message("[TEST] Ошибка записи coils для Канала 2")

        # Увеличиваем шаг
        self.snake_step += 1

        # Проверяем, нужно ли сбросить (все coils включены)
        if self.snake_step >= max(channel1_value, channel2_value):
            self.log_message("[TEST] Все coils включены - сброс и повтор")
            # Сбрасываем шаг
            self.snake_step = 0
            # Не выключаем coils, просто начинаем заново с включения coil 0

    def stop_snake_test(self):
        """Остановить тест змейки"""
        self.snake_active = False
        if hasattr(self, 'snake_timer'):
            self.snake_timer.stop()
            delattr(self, 'snake_timer')

        # Выключаем все coils
        channel1_value = self.channel1_spinbox.value()
        channel2_value = self.channel2_spinbox.value()

        if channel1_value > 0 and self.worker_thread:
            self.worker_thread.write_coils(0, [False] * channel1_value)
        if channel2_value > 0 and self.worker_thread:
            self.worker_thread.write_coils(32, [False] * channel2_value)

        self.log_message("[TEST] Тест змейки остановлен")

    def run_auto_test_cycle(self):
        """Циклическое выполнение автоматического тестирования"""
        if not self.connection_status or not self.config_read:
            self.stop_auto_testing()
            return

        # Определяем текущий режим и выполняем тест
        if self.running_lights_radio.isChecked():
            self.run_running_lights_test()
        elif self.full_switch_radio.isChecked():
            self.run_full_switch_test()
        elif self.snake_radio.isChecked():
            self.run_snake_test()

    def start_auto_testing(self):
        """Запуск автоматического тестирования"""
        if self.auto_testing_active:
            return

        self.auto_testing_active = True
        self.auto_test_timer.start()
        self.log_message("[AUTO TEST] Автоматическое тестирование запущено")

    def stop_auto_testing(self):
        """Остановка автоматического тестирования"""
        if not self.auto_testing_active:
            return

        self.auto_testing_active = False
        self.auto_test_timer.stop()
        self.log_message("[AUTO TEST] Автоматическое тестирование остановлено")

    def on_test_mode_changed(self):
        """Обработчик изменения режима тестирования"""
        self.log_message("[MODE] Смена режима тестирования - остановка предыдущего режима")
        self.stop_all_tests()

    def stop_all_tests(self):
        """Остановить все активные тесты"""
        # Останавливаем тест бегущих огней
        if hasattr(self, 'running_lights_active') and self.running_lights_active:
            self.stop_running_lights_test()

        # Останавливаем тест змейки
        if hasattr(self, 'snake_active') and self.snake_active:
            self.stop_snake_test()

        # Останавливаем автоматическое тестирование
        if self.auto_testing_active:
            self.stop_auto_testing()

        # Сбрасываем состояние полного переключения
        self.full_switch_state = False

        # Выключаем все coils
        channel1_value = self.channel1_spinbox.value()
        channel2_value = self.channel2_spinbox.value()

        if channel1_value > 0 and self.worker_thread:
            self.worker_thread.write_coils(0, [False] * channel1_value)
        if channel2_value > 0 and self.worker_thread:
            self.worker_thread.write_coils(32, [False] * channel2_value)

        self.log_message("[MODE] Все тесты остановлены, coils выключены")

    def toggle_auto_testing(self, state):
        """Переключение автоматического тестирования по чекбоксу"""
        if state == 2:  # Qt.Checked
            if self.connection_status and self.config_read:
                self.start_auto_testing()
            else:
                self.auto_test_checkbox.setChecked(False)
                QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к устройству и прочитайте конфигурацию")
        else:  # Qt.Unchecked
            self.stop_auto_testing()



    def update_ui(self):
        """Обновление интерфейса"""
        # Здесь можно добавить периодическое обновление UI
        # Автоматическое подключение убрано - пользователь сам решает когда подключаться
        pass

    def closeEvent(self, a0):
        """Закрытие приложения"""
        self.stop_auto_testing()  # останавливаем автоматическое тестирование
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.worker_thread.wait()
        if a0:
            a0.accept()

    def read_device_config(self):
        """Прочитать конфигурацию устройства (требует предварительного подключения)"""
        if not self.connection_status or not self.worker_thread:
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к устройству")
            return

        self.log_message("Чтение конфигурации устройства...")
        self.status_bar.showMessage("Чтение конфигурации...")

        # Пытаемся прочитать информацию об устройстве через команду 17
        device_info = self.worker_thread.read_device_info()

        if device_info:
            # Успешно прочитали через команду 17
            self.log_message("[OK] Конфигурация устройства прочитана успешно (команда 17)")
            self.status_bar.showMessage("Конфигурация прочитана")

            # Отображаем информацию о прошивке
            baudrate = getattr(self.worker_thread, 'baudrate', 38400)
            self.display_firmware_info(device_info, baudrate)

            # Читаем конфигурацию каналов и параметров
            self.read_channel_config()

            self.last_read_label.setText(f"Последнее чтение: {datetime.now().strftime('%H:%M:%S')}")

            # Устанавливаем флаг, что конфигурация прочитана
            self.config_read = True
            self.update_test_group_state()
        else:
            # Команда 17 не работает, пробуем прочитать регистры напрямую
            self.log_message("[INFO] Команда 17 не поддерживается, пробуем прочитать регистры напрямую...")
            self.status_bar.showMessage("Чтение регистров напрямую...")

            # Пробуем прочитать регистры напрямую
            direct_config = self.read_device_config_direct()

            if direct_config:
                # Успешно прочитали через регистры
                self.log_message("[OK] Конфигурация устройства прочитана успешно (прямое чтение регистров)")
                self.status_bar.showMessage("Конфигурация прочитана")

                # Отображаем информацию о регистрах
                address = self.address_spinbox.value()
                baudrate = getattr(self.worker_thread, 'baudrate', 38400)
                self.display_direct_config_info(direct_config, address, baudrate)

                # Конфигурация уже прочитана в read_device_config_direct()
                self.last_read_label.setText(f"Последнее чтение: {datetime.now().strftime('%H:%M:%S')}")

                # Устанавливаем флаг, что конфигурация прочитана
                self.config_read = True
                self.update_test_group_state()
            else:
                # Не удалось прочитать конфигурацию
                self.log_message("[FAIL] Не удалось прочитать конфигурацию устройства")
                self.status_bar.showMessage("Ошибка чтения конфигурации")

    def read_channel_config(self):
        """Прочитать конфигурацию каналов, Modbus RTU и CAN параметров из регистров 1, 2, 3, 6, 10, 11"""
        if not self.connection_status or not self.worker_thread:
            return

        self.log_message("Чтение конфигурации каналов, Modbus RTU и CAN параметров...")
        # Читаем регистры 1,2 (каналы), 3 (скорость Modbus), 6 (адрес Modbus), 10,11 (CAN параметры)
        register_data1 = self.worker_thread.read_holding_registers(1, 2)  # каналы
        register_data2 = self.worker_thread.read_holding_registers(3, 1)  # скорость Modbus
        register_data3 = self.worker_thread.read_holding_registers(6, 1)  # адрес Modbus
        register_data4 = self.worker_thread.read_holding_registers(10, 2) # CAN параметры

        if (register_data1 and "holding_registers" in register_data1 and
            register_data2 and "holding_registers" in register_data2 and
            register_data3 and "holding_registers" in register_data3 and
            register_data4 and "holding_registers" in register_data4):

            registers1 = register_data1["holding_registers"]  # каналы
            registers2 = register_data2["holding_registers"]  # скорость Modbus
            registers3 = register_data3["holding_registers"]  # адрес Modbus
            registers4 = register_data4["holding_registers"]  # CAN параметры

            if len(registers1) >= 2 and len(registers2) >= 1 and len(registers3) >= 1 and len(registers4) >= 2:
                # Каналы
                self.channel1_spinbox.setValue(registers1[0])
                self.channel2_spinbox.setValue(registers1[1])

                # Modbus RTU параметры
                modbus_speed_value = registers2[0]
                modbus_address_value = registers3[0]

                # Преобразование скорости Modbus из числового значения в текстовое
                modbus_speed_text = self._modbus_speed_value_to_text(modbus_speed_value)
                self.baudrate_combo.setCurrentText(modbus_speed_text)

                # Адрес Modbus
                if 1 <= modbus_address_value <= 247:
                    self.address_spinbox.setValue(modbus_address_value)

                # CAN параметры
                can_speed_value = registers4[0]
                can_address_value = registers4[1]

                # Преобразование скорости CAN из числового значения в текстовое
                can_speed_text = self._can_speed_value_to_text(can_speed_value)
                self.can_speed_combo.setCurrentText(can_speed_text)

                # Адрес CAN
                if 1 <= can_address_value <= 127:
                    self.can_address_combo.setCurrentText(str(can_address_value))

                self.log_message(f"[OK] Конфигурация прочитана: Канал 1={registers1[0]}, Канал 2={registers1[1]}, Modbus скорость={modbus_speed_text}, Modbus адрес={modbus_address_value}, CAN скорость={can_speed_text}, CAN адрес={can_address_value}")
            else:
                self.log_message("[FAIL] Недостаточно данных в регистрах")
        else:
            self.log_message("[FAIL] Не удалось прочитать конфигурацию")

    def write_device_config(self):
        """Записать конфигурацию каналов, Modbus RTU и CAN параметров на устройство"""
        if not self.connection_status or not self.worker_thread:
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к устройству")
            return

        # Получаем значения из полей каналов
        channel1_value = self.channel1_spinbox.value()
        channel2_value = self.channel2_spinbox.value()

        # Получаем значения Modbus RTU параметров
        modbus_speed_text = self.baudrate_combo.currentText()
        modbus_address_value = self.address_spinbox.value()

        # Получаем значения CAN параметров
        can_speed_text = self.can_speed_combo.currentText()
        can_address_text = self.can_address_combo.currentText()

        # Преобразование скоростей из текста в числовое значение
        modbus_speed_value = self._modbus_speed_text_to_value(modbus_speed_text)
        can_speed_value = self._can_speed_text_to_value(can_speed_text)
        can_address_value = int(can_address_text) if can_address_text.isdigit() else 2

        # Показываем диалог подтверждения с актуальными значениями
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы действительно хотите записать конфигурацию на устройство?\n\n"
            f"Канал 1: {channel1_value} катушек\n"
            f"Канал 2: {channel2_value} катушек\n"
            f"Modbus скорость: {modbus_speed_text}\n"
            f"Modbus адрес: {modbus_address_value}\n"
            f"CAN скорость: {can_speed_text}\n"
            f"CAN адрес: {can_address_value}\n\n"
            f"Это действие изменит настройки устройства.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        self.log_message("Запись конфигурации на устройство...")
        self.status_bar.showMessage("Запись конфигурации...")

        # Записываем значения каналов в регистры 1 и 2
        channel_values = [channel1_value, channel2_value]
        result1 = self.worker_thread.write_holding_registers(1, channel_values)

        # Записываем Modbus RTU параметры в регистры 3 и 6
        result2 = self.worker_thread.write_holding_registers(3, [modbus_speed_value])
        result4 = self.worker_thread.write_holding_registers(6, [modbus_address_value])

        # Записываем CAN параметры в регистры 10 и 11
        can_values = [can_speed_value, can_address_value]
        result3 = self.worker_thread.write_holding_registers(10, can_values)

        if (result1 and result1.get("status") == "success" and
            result2 and result2.get("status") == "success" and
            result4 and result4.get("status") == "success" and
            result3 and result3.get("status") == "success"):
            self.log_message("[OK] Конфигурация успешно записана на устройство")
            self.status_bar.showMessage("Конфигурация записана")
        else:
            error_msg = "Ошибка записи конфигурации"
            if result1 and result1.get("status") != "success":
                error_msg += " (каналы)"
            if result2 and result2.get("status") != "success":
                error_msg += " (Modbus скорость)"
            if result4 and result4.get("status") != "success":
                error_msg += " (Modbus адрес)"
            if result3 and result3.get("status") != "success":
                error_msg += " (CAN)"
            self.log_message(f"[FAIL] {error_msg}")
            self.status_bar.showMessage("Ошибка записи конфигурации")

    def read_device_config_direct(self):
        """Прочитать конфигурацию устройства через прямое чтение регистров"""
        if not self.worker_thread:
            return None

        self.log_message("Попытка прямого чтения регистров конфигурации...")

        try:
            # Добавляем задержку для инициализации устройства
            QThread.msleep(1000)
            self.log_message("Ожидание инициализации устройства...")

            # Сначала пробуем прочитать регистр 0 (нулевой адрес)
            self.log_message("Пробуем прочитать регистр 0...")
            register_data0 = self.worker_thread.read_holding_registers(0, 1)
            if register_data0 and "holding_registers" in register_data0:
                self.log_message(f"[OK] Регистр 0 прочитан: {register_data0['holding_registers']}")

            # Пробуем прочитать регистры 1, 2, 3, 6 (каналы, скорость, адрес)
            self.log_message("Пробуем прочитать регистры 1-2 (каналы)...")
            register_data1 = self.worker_thread.read_holding_registers(1, 2)  # каналы

            self.log_message("Пробуем прочитать регистр 3 (скорость Modbus)...")
            register_data2 = self.worker_thread.read_holding_registers(3, 1)  # скорость Modbus

            self.log_message("Пробуем прочитать регистр 6 (адрес Modbus)...")
            register_data3 = self.worker_thread.read_holding_registers(6, 1)  # адрес Modbus

            # Проверяем результаты
            success_count = 0
            if register_data1 and "holding_registers" in register_data1 and len(register_data1["holding_registers"]) >= 2:
                success_count += 1
                self.log_message(f"[OK] Регистры 1-2 прочитаны: {register_data1['holding_registers']}")
            else:
                self.log_message("[FAIL] Не удалось прочитать регистры 1-2")

            if register_data2 and "holding_registers" in register_data2 and len(register_data2["holding_registers"]) >= 1:
                success_count += 1
                self.log_message(f"[OK] Регистр 3 прочитан: {register_data2['holding_registers']}")
            else:
                self.log_message("[FAIL] Не удалось прочитать регистр 3")

            if register_data3 and "holding_registers" in register_data3 and len(register_data3["holding_registers"]) >= 1:
                success_count += 1
                self.log_message(f"[OK] Регистр 6 прочитан: {register_data3['holding_registers']}")
            else:
                self.log_message("[FAIL] Не удалось прочитать регистр 6")

            if success_count >= 2:  # Если прочитали хотя бы 2 из 3 групп регистров
                # Используем доступные данные
                config = {}

                if register_data1 and "holding_registers" in register_data1 and len(register_data1["holding_registers"]) >= 2:
                    registers1 = register_data1["holding_registers"]
                    config["channel1"] = registers1[0]
                    config["channel2"] = registers1[1]

                if register_data2 and "holding_registers" in register_data2 and len(register_data2["holding_registers"]) >= 1:
                    config["modbus_speed_value"] = register_data2["holding_registers"][0]

                if register_data3 and "holding_registers" in register_data3 and len(register_data3["holding_registers"]) >= 1:
                    config["modbus_address"] = register_data3["holding_registers"][0]

                config["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Обновляем GUI только для прочитанных значений
                if "channel1" in config:
                    self.channel1_spinbox.setValue(config["channel1"])
                if "channel2" in config:
                    self.channel2_spinbox.setValue(config["channel2"])

                if "modbus_speed_value" in config:
                    modbus_speed_text = self._modbus_speed_value_to_text(config["modbus_speed_value"])
                    self.baudrate_combo.setCurrentText(modbus_speed_text)

                if "modbus_address" in config and 1 <= config["modbus_address"] <= 247:
                    self.address_spinbox.setValue(config["modbus_address"])

                self.log_message(f"[OK] Конфигурация прочитана частично: {config}")
                return config
            else:
                self.log_message(f"[FAIL] Прочитано только {success_count} из 3 групп регистров")
                return None

        except Exception as e:
            self.log_message(f"[ERROR] Ошибка при прямом чтении регистров: {str(e)}")
            return None

    def display_direct_config_info(self, config: dict, address: int, baudrate: int):
        """Отобразить информацию о конфигурации, прочитанной напрямую из регистров"""
        if not config:
            self.firmware_text.setPlainText("Информация о конфигурации недоступна")
            return

        config_text = f"Конфигурация устройства (прямое чтение регистров)\n"
        config_text += f"Адрес: {address}, Скорость: {baudrate} baud\n"
        config_text += "=" * 60 + "\n\n"

        config_text += "Прочитанные регистры:\n"
        config_text += "-" * 30 + "\n"
        config_text += f"Регистр 1 (Канал 1): {config.get('channel1', 'N/A')}\n"
        config_text += f"Регистр 2 (Канал 2): {config.get('channel2', 'N/A')}\n"
        config_text += f"Регистр 3 (Modbus скорость): {config.get('modbus_speed_value', 'N/A')} ({self._modbus_speed_value_to_text(config.get('modbus_speed_value', 2))})\n"
        config_text += f"Регистр 6 (Modbus адрес): {config.get('modbus_address', 'N/A')}\n\n"

        config_text += "Интерпретация:\n"
        config_text += "-" * 20 + "\n"
        config_text += f"Количество катушек Канал 1: {config.get('channel1', 'N/A')}\n"
        config_text += f"Количество катушек Канал 2: {config.get('channel2', 'N/A')}\n"
        config_text += f"Скорость Modbus RTU: {self._modbus_speed_value_to_text(config.get('modbus_speed_value', 2))}\n"
        config_text += f"Адрес устройства: {config.get('modbus_address', 'N/A')}\n\n"

        config_text += f"Время чтения: {config.get('timestamp', 'N/A')}"

        self.firmware_text.setPlainText(config_text)

    def display_firmware_info(self, device_info: dict, baudrate: int):
        """Отобразить информацию о прошивке в отдельной области"""
        if not device_info or not isinstance(device_info, dict):
            self.firmware_text.setPlainText("Информация о прошивке недоступна")
            return

        # Hex формат ответа
        hex_response = device_info.get('raw_hex') or device_info.get('hex_format') or device_info.get('raw_response')
        if not hex_response:
            self.firmware_text.setPlainText("Информация о прошивке недоступна")
            return

        firmware_text = f"Ответ: {hex_response}\n"
        firmware_text += "Версия прошивки:\n"
        firmware_text += "-" * 50 + "\n"

        # Извлекаем device_specific_data если есть
        device_data = device_info.get("device_specific_data", {})

        # Основные поля согласно спецификации
        if "product_id" in device_data:
            pid = device_data["product_id"]
            firmware_text += f"ProductID: {pid.get('value', 'N/A')}\n"

        if "status" in device_data:
            status = device_data["status"]
            firmware_text += f"Status: {status.get('value', 'N/A')}\n"

        if "magic" in device_data:
            magic = device_data["magic"]
            firmware_text += f"Magic: {magic.get('value', 'N/A')}\n"

        if "hardware" in device_data:
            hw = device_data["hardware"]
            firmware_text += f"Hardware: {hw.get('value', 'N/A')}\n"

        if "software" in device_data:
            sw = device_data["software"]
            firmware_text += f"Software: {sw.get('value', 'N/A')}\n"

        if "io_counts" in device_data:
            io = device_data["io_counts"]
            firmware_text += f"DI/DO/AI/AO: {io.get('value', 'N/A')}\n"

        if "ver_status" in device_data:
            vs = device_data["ver_status"]
            firmware_text += f"VerStatus: {vs.get('value', 'N/A')}\n"

        self.firmware_text.setPlainText(firmware_text)

    def _scan_available_ports(self):
        """Сканировать доступные COM порты и обновить список"""
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            available_ports = []

            for port in ports:
                available_ports.append(port.device)

            # Добавляем стандартные порты на всякий случай
            default_ports = ["COM1", "COM2", "COM3", "COM4", "COM5", "/dev/ttyUSB0", "/dev/ttyUSB1"]
            for port in default_ports:
                if port not in available_ports:
                    available_ports.append(port)

            # Обновляем combo box
            current_text = self.port_combo.currentText()
            self.port_combo.clear()
            self.port_combo.addItems(available_ports)

            # Восстанавливаем выбранный текст если он был
            if current_text in available_ports:
                self.port_combo.setCurrentText(current_text)
            elif available_ports:
                self.port_combo.setCurrentText(available_ports[0])

            self.log_message(f"Найдено {len(ports)} доступных портов: {', '.join([p.device for p in ports])}")

        except ImportError:
            # Если serial.tools.list_ports недоступен, используем стандартный список
            default_ports = ["COM1", "COM2", "COM3", "COM4", "COM5", "/dev/ttyUSB0", "/dev/ttyUSB1"]
            current_text = self.port_combo.currentText()
            self.port_combo.clear()
            self.port_combo.addItems(default_ports)
            if current_text in default_ports:
                self.port_combo.setCurrentText(current_text)
            self.log_message("Используется список портов по умолчанию")
        except Exception as e:
            self.log_message(f"Ошибка сканирования портов: {str(e)}")

    def _is_port_available(self, port: str) -> bool:
        """Проверить доступность COM порта"""
        try:
            import serial
            # Пытаемся открыть порт для проверки
            ser = serial.Serial(port, 9600, timeout=1)
            ser.close()
            return True
        except Exception as e:
            self.log_message(f"Порт {port} недоступен: {str(e)}")
            return False

    def _modbus_speed_value_to_text(self, value: int) -> str:
        """Преобразовать числовое значение скорости Modbus RTU в текстовое"""
        speed_map = {
            0: "2400",
            1: "4800",
            2: "9600",
            3: "19200",
            4: "38400",
            5: "57600",
            6: "115200"
        }
        return speed_map.get(value, "9600")  # По умолчанию 9600

    def _modbus_speed_text_to_value(self, text: str) -> int:
        """Преобразовать текстовое значение скорости Modbus RTU в числовое"""
        speed_map = {
            "2400": 0,
            "4800": 1,
            "9600": 2,
            "19200": 3,
            "38400": 4,
            "57600": 5,
            "115200": 6
        }
        return speed_map.get(text, 2)  # По умолчанию 2 (9600)

    def _can_speed_value_to_text(self, value: int) -> str:
        """Преобразовать числовое значение скорости CAN в текстовое"""
        speed_map = {
            0: "10K",
            1: "20K",
            2: "50K",
            3: "125K",
            4: "250K",
            5: "500K",
            6: "800K",
            7: "1000K"
        }
        return speed_map.get(value, "1000K")  # По умолчанию 1000K

    def _can_speed_text_to_value(self, text: str) -> int:
        """Преобразовать текстовое значение скорости CAN в числовое"""
        speed_map = {
            "10K": 0,
            "20K": 1,
            "50K": 2,
            "125K": 3,
            "250K": 4,
            "500K": 5,
            "800K": 6,
            "1000K": 7
        }
        return speed_map.get(text, 7)  # По умолчанию 7 (1000K)

    def log_message(self, message: str):
        """Добавить сообщение в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        current_text = self.output_text.toPlainText()
        self.output_text.setPlainText(current_text + log_entry)

        # Автоматическая прокрутка вниз
        cursor = self.output_text.textCursor()
        cursor.movePosition(cursor.End)
        self.output_text.setTextCursor(cursor)

if __name__ == '__main__':
    """Главная функция запуска приложения"""
    try:
        # Создаем приложение
        app = QApplication(sys.argv)
        app.setApplicationName("Modbus RTU Scanner GUI")
        app.setApplicationVersion("1.0")
        
        # Создаем и показываем главное окно
        window = ModbusRTUGUI()
        window.show()
        
        print("[GUI] Приложение запущено. Для выхода закройте окно.")
        
        # Запускаем цикл событий
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"[GUI] Критическая ошибка при запуске: {e}")
        import traceback
        traceback.print_exc()
        
        # Попытка показать сообщение об ошибке если GUI не запустился
        try:
            from PyQt5.QtWidgets import QMessageBox
            error_app = QApplication(sys.argv)
            QMessageBox.critical(None, "Критическая ошибка", 
                               f"Не удалось запустить приложение:\n\n{str(e)}")
        except:
            pass
            
        sys.exit(1)
