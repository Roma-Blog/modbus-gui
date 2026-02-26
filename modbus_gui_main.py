#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modbus GUI Main Module (Refactored)
Главный модуль GUI приложения Modbus RTU Scanner (рефакторинг)
"""

import sys
import os
from datetime import datetime

# PyQt5 импорты
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QStatusBar, QProgressBar,
    QTabWidget, QMessageBox, QGroupBox, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

# Добавляем путь для импорта наших модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
core_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'core')
sys.path.insert(0, core_path)

from modbus_worker import ModbusWorkerThread
from connection_tab import ConnectionTab
from config_manager import ConfigManager
from test_controller import TestController
from firmware_display import FirmwareDisplay
from constants import DEFAULT_COM_PORTS, TIMER_INTERVALS, AUTO_SEARCH_CONFIG
from auto_search_worker import AutoSearchWorker


class ModbusRTUGUI(QMainWindow):
    """Главное окно приложения Modbus RTU (рефакторинг)"""

    def __init__(self):
        super().__init__()
        self.worker_thread = None
        self.auto_search_worker = None
        self.connection_status = False
        self.config_read = False
        self.port_opened = False

        # Инициализация компонентов
        self.config_manager = None
        self.test_controller = None
        self.connection_tab = None
        self.firmware_display = None

        # UI компоненты
        self.connection_info_label = None
        self.last_read_label = None
        self.status_bar = None
        self.progress_bar = None
        self.tab_widget = None

        self.init_ui()
        self.setup_components()
        self.setup_timers()

        # Сканируем доступные COM порты
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
        main_layout = QVBoxLayout(central_widget)

        # Создаем вкладки
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

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

    def setup_components(self):
        """Настройка компонентов"""
        # Создаем дисплей прошивки
        self.firmware_display = FirmwareDisplay(self)

        # Создаем вкладку подключения
        self.connection_tab = ConnectionTab(self)
        self.tab_widget.addTab(self.connection_tab, "Подключение")

        # Добавляем дисплей прошивки в row2_layout вкладки подключения (справа от "Проверка")
        self.connection_tab.add_firmware_display(self.firmware_display.get_widget())

        # Создаем менеджер конфигурации
        self.config_manager = ConfigManager(self.worker_thread)

        # Создаем контроллер тестирования
        self.test_controller = TestController(self.worker_thread, self.log_message)

        # Связываем компоненты
        self.connection_tab.set_config_manager(self.config_manager)

    def setup_timers(self):
        """Настройка таймеров"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.setInterval(TIMER_INTERVALS["UPDATE_UI"])
        self.update_timer.start()

    def toggle_connection(self):
        """Переключение состояния соединения"""
        if not self.port_opened:
            self.connect()
        else:
            self.disconnect_connection()

    def connect(self):
        """Подключение к устройству через Modbus RTU"""
        params = self.connection_tab.get_connection_params()
        port = params["port"]
        address = params["address"]
        baudrate_text = params["baudrate"]

        if not port:
            QMessageBox.warning(self, "Ошибка", "Выберите COM порт")
            return

        # Проверяем доступность порта
        if not self._is_port_available(port):
            QMessageBox.warning(self, "Ошибка", f"Порт {port} недоступен")
            return

        # Проверяем, включен ли автопоиск
        if self.connection_tab.is_auto_search_enabled():
            self._start_auto_search(port)
            return

        # Обычное подключение без автопоиска
        self._connect_without_search(port, address, baudrate_text)

    def _connect_without_search(self, port: str, address: int, baudrate_text: str):
        """
        Обычное подключение без автопоиска

        Args:
            port: COM порт
            address: Адрес устройства
            baudrate_text: Скорость соединения (текст)
        """
        # Устанавливаем флаг, что порт открыт
        self.port_opened = True
        self.connection_tab.update_connection_buttons(True)

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

        # Обновляем компоненты с новым worker_thread
        self.config_manager.worker_thread = self.worker_thread
        self.test_controller.worker_thread = self.worker_thread

        # Ждем немного для инициализации (увеличенный таймаут для устройств с медленным откликом)
        QTimer.singleShot(5000, self._check_connection_timeout)  # 5 секунд вместо 2

    def _start_auto_search(self, port: str):
        """
        Запуск автоматического поиска устройства

        Args:
            port: COM порт для сканирования
        """
        self.log_message("[AUTO SEARCH] Запуск автоматического поиска устройства...")
        self.log_message("[AUTO SEARCH] Алгоритм: для каждого адреса (1-200) перебираем все скорости (115200→9600)")

        # Показываем прогресс поиска
        self.connection_tab.set_search_progress(True, "Инициализация сканера...")
        self.status_bar.showMessage("Автопоиск устройства...")

        # Блокируем кнопку подключения
        self.connection_tab.connect_btn.setEnabled(False)

        # Создаем и запускаем поток автопоиска
        self.auto_search_worker = AutoSearchWorker(port, timeout_ms=AUTO_SEARCH_CONFIG["TIMEOUT_MS"])
        self.auto_search_worker.device_found.connect(self._on_device_found)
        self.auto_search_worker.search_progress.connect(self._on_search_progress)
        self.auto_search_worker.search_complete.connect(self._on_search_complete)
        self.auto_search_worker.error_occurred.connect(self._on_search_error)
        self.auto_search_worker.start()

    def _on_device_found(self, device_info: dict):
        """
        Обнаружено устройство при автопоиске

        Args:
            device_info: {'address': int, 'baudrate': int, 'device_info': dict}
        """
        address = device_info['address']
        baudrate = device_info['baudrate']

        self.log_message(f"[AUTO SEARCH] ✓ Устройство найдено: адрес {address}, скорость {baudrate} baud")

        # Обновляем UI с найденными параметрами
        self.connection_tab.address_spinbox.setValue(address)
        self.connection_tab.baudrate_combo.setCurrentText(str(baudrate))

        # Сохраняем найденную информацию о устройстве
        self._found_device_info = device_info

    def _on_search_progress(self, status: str):
        """
        Обновление статуса поиска

        Args:
            status: Текст статуса
        """
        self.connection_tab.set_search_progress(True, status)
        self.log_message(f"[AUTO SEARCH] {status}")

    def _on_search_complete(self, success: bool, message: str):
        """
        Завершение поиска

        Args:
            success: Успешно ли найдено устройство
            message: Сообщение статуса
        """
        # Скрываем прогресс
        self.connection_tab.set_search_progress(False)
        self.connection_tab.connect_btn.setEnabled(True)

        if success:
            # Устройство найдено - подключаемся
            self.log_message(f"[AUTO SEARCH] {message}")
            self.status_bar.showMessage(message)

            # Подключаемся на найденных параметрах
            device_info = getattr(self, '_found_device_info', None)
            if device_info:
                self._connect_after_auto_search(device_info)
            else:
                # Если device_info не сохранен, используем текущие значения из UI
                params = self.connection_tab.get_connection_params()
                self._connect_without_search(
                    params["port"],
                    params["address"],
                    str(params["baudrate"])
                )
        else:
            # Устройство не найдено
            self.log_message(f"[AUTO SEARCH] {message}")
            self.status_bar.showMessage(message)
            QMessageBox.warning(
                self, "Автопоиск",
                f"Устройство не найдено.\n\n{message}\n\n"
                f"Проверьте:\n"
                f"- Подключено ли устройство к порту {self.connection_tab.port_combo.currentText()}\n"
                f"- Исправность кабеля и преобразователя RS-485/USB\n"
                f"- Наличие питания устройства"
            )

    def _on_search_error(self, error_message: str):
        """
        Ошибка автопоиска

        Args:
            error_message: Сообщение об ошибке
        """
        self.connection_tab.set_search_progress(False)
        self.connection_tab.connect_btn.setEnabled(True)
        self.log_message(f"[AUTO SEARCH] Ошибка: {error_message}")
        self.status_bar.showMessage("Ошибка автопоиска")
        QMessageBox.critical(self, "Ошибка автопоиска", error_message)

    def _connect_after_auto_search(self, device_info: dict):
        """
        Подключение после успешного автопоиска

        Args:
            device_info: Информация о найденном устройстве
        """
        address = device_info['address']
        baudrate = device_info['baudrate']
        params = self.connection_tab.get_connection_params()
        port = params["port"]

        self.log_message(f"[AUTO SEARCH] Подключение на найденных параметрах: порт {port}, адрес {address}, скорость {baudrate}")

        # Устанавливаем флаг, что порт открыт
        self.port_opened = True
        self.connection_tab.update_connection_buttons(True)

        # Показываем прогресс
        self.progress_bar.setVisible(True)
        self.status_bar.showMessage("Подключение к устройству...")

        # Создаем worker_thread для подключения
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.worker_thread.wait()

        self.worker_thread = ModbusWorkerThread(port, address, baudrate)
        self.worker_thread.connected.connect(self.on_connected)
        self.worker_thread.error_occurred.connect(self.on_error_occurred)
        self.worker_thread.status_updated.connect(self.on_status_updated)
        self.worker_thread.start()

        # Обновляем компоненты с новым worker_thread
        self.config_manager.worker_thread = self.worker_thread
        self.test_controller.worker_thread = self.worker_thread

        # Ждем немного для инициализации
        QTimer.singleShot(5000, self._check_connection_timeout)

    def _check_connection_timeout(self):
        """Проверить таймаут подключения и запустить поиск адреса при необходимости"""
        if not self.connection_status and self.worker_thread:
            # Подключение не удалось - проверяем, нужно ли запускать поиск адреса
            params = self.connection_tab.get_connection_params()
            port = params["port"]
            baudrate_text = params["baudrate"]
            user_address = params["address"]

            if baudrate_text == "Автоопределение":
                self.log_message("[INFO] Автоопределение скорости не поддерживается при подключении - выберите фиксированную скорость")
                self.progress_bar.setVisible(False)
                self.connection_info_label.setText("Ошибка: выберите фиксированную скорость")
                self.connection_info_label.setStyleSheet("QLabel { font-weight: bold; color: red; }")
                self.status_bar.showMessage("Ошибка подключения")
                self.port_opened = False
                self.connection_tab.update_connection_buttons(False)
                return

            baudrate = int(baudrate_text)

            # Если пользователь указал адрес отличный от 4, не делаем автоопределение
            if user_address != 4:
                self.log_message(f"[INFO] Устройство не отвечает на указанный адрес {user_address}. Проверьте параметры подключения.")
                self.log_message(f"[DEBUG] Параметры: порт={port}, адрес={user_address}, скорость={baudrate}")
                self.on_connected(False, f"Устройство не отвечает на адресе {user_address}")
                return

            # Если адрес по умолчанию (4), запускаем поиск адреса
            self.log_message(f"[INFO] Устройство не отвечает на адрес {user_address}, запускаем поиск адреса...")

            # Запускаем поиск адреса
            device_info, found_address = self.worker_thread.auto_detect_address_with_command17(port, baudrate)

            if device_info and found_address:
                # Устройство найдено - обновляем GUI и подключаемся
                self.connection_tab.address_spinbox.setValue(found_address)
                self.firmware_display.display_firmware_info(device_info, baudrate)

                # Читаем конфигурацию каналов
                self.read_channel_config()

                # Автоматически читаем Modbus RTU параметры, но не перезаписываем адрес
                # (адрес уже установлен найденным через поиск)
                modbus_config = self.config_manager.read_modbus_rtu_config_from_device()
                if modbus_config:
                    # Создаем копию конфигурации без адреса, чтобы не перезаписывать найденный
                    modbus_config_without_address = modbus_config.copy()
                    modbus_config_without_address.pop('modbus_address', None)
                    if modbus_config_without_address:
                        self.connection_tab.set_modbus_config(modbus_config_without_address)

                    # Логируем разницу между найденным и сохраненным адресом
                    saved_address = modbus_config.get('modbus_address')
                    if saved_address and saved_address != found_address:
                        self.log_message(f"[INFO] Устройство найдено на адресе {found_address}, но в конфигурации сохранен адрес {saved_address}")

                self.on_connected(True, f"Устройство найдено на адресе {found_address}")
            else:
                # Устройство не найдено
                self.on_connected(False, "Устройство не найдено на доступных адресах")

    def disconnect_connection(self):
        """Отключение от устройства и закрытие порта"""
        if self.worker_thread:
            self.worker_thread.stop()
            self.worker_thread.wait()
            self.worker_thread = None

        self.connection_status = False
        self.config_read = False
        self.test_controller.stop_all_tests()
        self.connection_tab.update_connection_buttons(False)
        self.connection_tab.reset_channel_config()

        self.status_bar.showMessage("Отключено")
        self.log_message("Соединение с устройством отключено пользователем")

        # Сбрасываем флаг открытия порта
        self.port_opened = False

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
            self.connection_tab.update_connection_buttons(True)

            # Автоматически читаем конфигурацию при успешном подключении
            if "найдено на адресе" in message.lower():
                # Устройство найдено через поиск адреса - читаем конфигурацию
                self.read_channel_config()
                self.config_read = True
                self.connection_tab.update_test_group_state(True)
        else:
            self.connection_status = False
            self.connection_info_label.setText(message)
            self.connection_info_label.setStyleSheet("QLabel { font-weight: bold; color: red; }")
            self.status_bar.showMessage("Ошибка подключения")
            self.log_message(f"[FAIL] {message}")
            self.connection_tab.update_connection_buttons(False)

    def on_error_occurred(self, error_message: str):
        """Обработка ошибок"""
        self.log_message(f"Ошибка: {error_message}")
        if not self.connection_status:
            self.progress_bar.setVisible(False)
            self.connection_tab.update_connection_buttons(False)

    def on_status_updated(self, status_message: str):
        """Обработка обновлений статуса"""
        self.log_message(f"[STATUS] {status_message}")
        self.status_bar.showMessage(status_message)

    def on_test_mode_changed(self):
        """Обработчик изменения режима тестирования"""
        self.log_message("[MODE] Смена режима тестирования - остановка предыдущего режима")
        self.test_controller.stop_all_tests()

    def toggle_auto_testing(self, state):
        """Переключение автоматического тестирования по чекбоксу"""
        if state == 2:  # Qt.Checked
            if self.connection_status and self.config_read:
                self.test_controller.start_auto_testing()
            else:
                self.connection_tab.auto_test_checkbox.setChecked(False)
                QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к устройству и прочитайте конфигурацию")
        else:  # Qt.Unchecked
            self.test_controller.stop_auto_testing()

    def run_test(self):
        """Запуск тестирования устройства"""
        if not self.connection_status or not self.worker_thread:
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к устройству")
            return

        # Получаем конфигурацию тестирования
        test_config = self.connection_tab.get_test_config()

        # Устанавливаем значения каналов для тестера
        channel_config = self.connection_tab.get_channel_config()
        self.test_controller.set_channel_values(
            channel_config["channel1"],
            channel_config["channel2"]
        )

        # Запускаем тест
        self.test_controller.run_test(
            mode=test_config["mode"],
            auto=test_config["auto"]
        )

    def read_device_config(self):
        """Прочитать конфигурацию устройства"""
        if not self.connection_status or not self.worker_thread:
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к устройству")
            return

        # Логируем параметры подключения для диагностики
        current_address = getattr(self.worker_thread, 'address', 'неизвестен')
        current_port = getattr(self.worker_thread, 'port', 'неизвестен')
        current_baudrate = getattr(self.worker_thread, 'baudrate', 'неизвестен')
        self.log_message(f"Чтение конфигурации устройства: порт {current_port}, адрес {current_address}, скорость {current_baudrate}")
        self.status_bar.showMessage("Чтение конфигурации...")

        # Пытаемся прочитать информацию об устройстве через команду 17
        self.log_message(f"[DEBUG] Попытка чтения device_info через команду 17 на адресе {current_address}")
        device_info = self.worker_thread.read_device_info()
        self.log_message(f"[DEBUG] Результат чтения device_info: {device_info is not None}")

        if device_info:
            # Успешно прочитали через команду 17
            self.log_message("[OK] Конфигурация устройства прочитана успешно (команда 17)")
            self.status_bar.showMessage("Конфигурация прочитана")

            # Отображаем информацию о прошивке
            baudrate = getattr(self.worker_thread, 'baudrate', 38400)
            self.firmware_display.display_firmware_info(device_info, baudrate)

            # Читаем конфигурацию каналов и параметров
            self.read_channel_config()

            self.last_read_label.setText(f"Последнее чтение: {datetime.now().strftime('%H:%M:%S')}")

            # Устанавливаем флаг, что конфигурация прочитана
            self.config_read = True
            self.connection_tab.update_test_group_state(True)
        else:
            # Команда 17 не работает на текущем адресе
            self.log_message("[FAIL] Не удалось прочитать конфигурацию устройства (команда 17 не поддерживается)")
            self.status_bar.showMessage("Ошибка чтения конфигурации")

    def read_channel_config(self):
        """Прочитать конфигурацию каналов"""
        config = self.config_manager.read_device_config()
        if config:
            # Обновляем UI
            if "channel1" in config:
                self.connection_tab.set_channel_config({
                    "channel1": config["channel1"],
                    "channel2": config.get("channel2", 0)
                })

            if "modbus_speed_text" in config:
                self.connection_tab.set_modbus_config({
                    "modbus_speed_text": config["modbus_speed_text"],
                    "modbus_address": config.get("modbus_address", 4)
                })

            if "can_speed_text" in config and "can_address" in config:
                self.connection_tab.set_can_config({
                    "can_speed_text": config["can_speed_text"],
                    "can_address": config["can_address"]
                })

            self.log_message(f"[OK] Конфигурация прочитана: Канал 1={config.get('channel1', 'N/A')}, Канал 2={config.get('channel2', 'N/A')}")


    def write_device_config(self):
        """Записать конфигурацию на устройство"""
        if not self.connection_status or not self.worker_thread:
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к устройству")
            return

        # Получаем конфигурацию из UI
        channel_config = self.connection_tab.get_channel_config()
        modbus_config = self.connection_tab.get_modbus_config()
        can_config = self.connection_tab.get_can_config()

        # Объединяем конфигурацию
        config = {**channel_config, **modbus_config, **can_config}

        # Показываем диалог подтверждения
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы действительно хотите записать конфигурацию на устройство?\n\n"
            f"Канал 1: {config.get('channel1', 'N/A')} катушек\n"
            f"Канал 2: {config.get('channel2', 'N/A')} катушек\n"
            f"Modbus скорость: {config.get('modbus_speed_text', 'N/A')}\n"
            f"Modbus адрес: {config.get('modbus_address', 'N/A')}\n"
            f"CAN скорость: {config.get('can_speed_text', 'N/A')}\n"
            f"CAN адрес: {config.get('can_address', 'N/A')}\n\n"
            f"Это действие изменит настройки устройства.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        self.log_message("Запись конфигурации на устройство...")
        self.status_bar.showMessage("Запись конфигурации...")

        # Записываем конфигурацию
        success = self.config_manager.write_device_config(config)

        if success:
            self.log_message("[OK] Конфигурация успешно записана на устройство")
            self.status_bar.showMessage("Конфигурация записана")
        else:
            self.log_message("[FAIL] Ошибка записи конфигурации")
            self.status_bar.showMessage("Ошибка записи конфигурации")

    def update_ui(self):
        """Обновление интерфейса"""
        # Здесь можно добавить периодическое обновление UI
        # Автоматическое подключение убрано - пользователь сам решает когда подключаться
        pass

    def closeEvent(self, a0):
        """Закрытие приложения"""
        self.test_controller.stop_all_tests()
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.worker_thread.wait()
        # Останавливаем автопоиск если он запущен
        if self.auto_search_worker and self.auto_search_worker.isRunning():
            self.auto_search_worker.stop_and_wait()
        if a0:
            a0.accept()

    def _scan_available_ports(self):
        """Сканировать доступные COM порты и обновить список"""
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            available_ports = []

            for port in ports:
                available_ports.append(port.device)

            # Добавляем стандартные порты на всякий случай
            for port in DEFAULT_COM_PORTS:
                if port not in available_ports:
                    available_ports.append(port)

            # Обновляем combo box
            current_text = self.connection_tab.port_combo.currentText()
            self.connection_tab.port_combo.clear()
            self.connection_tab.port_combo.addItems(available_ports)

            # Восстанавливаем выбранный текст если он был
            if current_text in available_ports:
                self.connection_tab.port_combo.setCurrentText(current_text)
            elif available_ports:
                self.connection_tab.port_combo.setCurrentText(available_ports[0])

            self.log_message(f"Найдено {len(ports)} доступных портов: {', '.join([p.device for p in ports])}")

        except ImportError:
            # Если serial.tools.list_ports недоступен, используем стандартный список
            current_text = self.connection_tab.port_combo.currentText()
            self.connection_tab.port_combo.clear()
            self.connection_tab.port_combo.addItems(DEFAULT_COM_PORTS)
            if current_text in DEFAULT_COM_PORTS:
                self.connection_tab.port_combo.setCurrentText(current_text)
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

    def log_message(self, message: str):
        """Добавить сообщение в лог"""
        if hasattr(self.connection_tab, 'output_text'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"

            current_text = self.connection_tab.output_text.toPlainText()
            self.connection_tab.output_text.setPlainText(current_text + log_entry)

            # Автоматическая прокрутка вниз
            cursor = self.connection_tab.output_text.textCursor()
            cursor.movePosition(cursor.End)
            self.connection_tab.output_text.setTextCursor(cursor)


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
