#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 3: Config - Шаг конфигурации устройства
"""

import sys
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QComboBox, QGroupBox, QGridLayout, QFrame,
    QSpacerItem, QSizePolicy, QMessageBox, QProgressBar
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .components.log_viewer import LogViewer
from .config_worker import ConfigReadWorker, ConfigWriteWorker
from constants import (
    DEFAULT_BAUDRATES, DEFAULT_CAN_SPEEDS, DEFAULT_CAN_ADDRESSES,
    LIMITS
)


class StepConfig(QWidget):
    """
    Шаг 3: Конфигурация

    Функции:
    - Отображение текущей конфигурации
    - Чтение конфигурации из устройства
    - Запись конфигурации в устройство
    - Кнопка открытия окна тестирования
    - Логи операций
    - Информация о прошивке
    """

    # Сигналы для уведомления главного окна
    config_written = pyqtSignal()  # Конфигурация записана - нужна перезагрузка
    config_read = pyqtSignal(dict)  # Конфигурация прочитана

    def __init__(self, parent=None):
        super().__init__(parent)

        # Состояние
        self.config_loaded = False
        self.config_data = {}
        self.worker_thread = None
        self.config_manager = None
        self.test_window = None

        # Worker потоки
        self.read_worker = None
        self.write_worker = None

        # Ссылка на главный окно (устанавливается из wizard_main)
        self.main_window = None

        self.init_ui()

    def init_ui(self):
        """Инициализация UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # Заголовок
        title = QLabel("Конфигурация устройства")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("QLabel { color: #2c3e50; }")
        layout.addWidget(title)

        # Основной контент (две колонки)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Левая колонка - настройки
        left_column = QVBoxLayout()
        left_column.setSpacing(15)

        # Группа конфигурации каналов
        channels_group = self._create_channels_group()
        left_column.addWidget(channels_group)

        # Группа Modbus параметров
        modbus_group = self._create_modbus_group()
        left_column.addWidget(modbus_group)

        # Группа CAN параметров
        can_group = self._create_can_group()
        left_column.addWidget(can_group)

        left_column.addStretch()
        content_layout.addLayout(left_column)

        # Правая колонка - прошивка и логи
        right_column = QVBoxLayout()
        right_column.setSpacing(15)

        # Информация о прошивке
        firmware_group = self._create_firmware_group()
        right_column.addWidget(firmware_group)

        # Логи
        self.log_viewer = LogViewer(title="Логи операций")
        self.log_viewer.log_text.setMaximumHeight(200)
        right_column.addWidget(self.log_viewer)

        content_layout.addLayout(right_column)
        content_layout.setStretch(0, 1)  # Левая колонка
        content_layout.setStretch(1, 1)  # Правая колонка

        layout.addLayout(content_layout)

        # Прогресс бар операций
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Непрерывная анимация
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #ecf0f1;
                border: none;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Статус операции
        self.operation_status_label = QLabel("")
        self.operation_status_label.setFont(QFont("Arial", 10))
        self.operation_status_label.setStyleSheet("QLabel { color: #7f8c8d; font-style: italic; }")
        self.operation_status_label.setVisible(False)
        layout.addWidget(self.operation_status_label)

        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("QFrame { background-color: #bdc3c7; }")
        layout.addWidget(line)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        # Кнопка тестирования
        # self.test_btn = QPushButton("Тестирование")
        # self.test_btn.setFont(QFont("Arial", 11))
        # self.test_btn.setMinimumSize(140, 40)
        # self.test_btn.clicked.connect(self.open_test_window)
        # self.test_btn.setEnabled(False)
        # self.test_btn.setStyleSheet("""
        #     QPushButton {
        #         background-color: #9b59b6;
        #         color: white;
        #         border: none;
        #         padding: 10px 16px;
        #         border-radius: 4px;
        #         font-weight: bold;
        #     }
        #     QPushButton:hover {
        #         background-color: #8e44ad;
        #     }
        #     QPushButton:disabled {
        #         background-color: #bdc3c7;
        #     }
        # """)
        # btn_layout.addWidget(self.test_btn)

        btn_layout.addStretch()

        # Кнопка чтения
        self.read_btn = QPushButton("Прочитать")
        self.read_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.read_btn.setMinimumSize(130, 40)
        self.read_btn.clicked.connect(self.read_config)
        self.read_btn.setEnabled(False)
        self.read_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        btn_layout.addWidget(self.read_btn)

        # Кнопка записи
        self.write_btn = QPushButton("Записать")
        self.write_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.write_btn.setMinimumSize(130, 40)
        self.write_btn.clicked.connect(self.write_config)
        self.write_btn.setEnabled(False)
        self.write_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        btn_layout.addWidget(self.write_btn)

        layout.addLayout(btn_layout)

    def _create_channels_group(self) -> QGroupBox:
        """Создать группу конфигурации каналов"""
        group = QGroupBox("Каналы")
        layout = QGridLayout(group)
        layout.setHorizontalSpacing(15)
        layout.setVerticalSpacing(10)

        # Канал 1
        channel1_label = QLabel("Канал 1 (катушек):")
        channel1_label.setFont(QFont("Arial", 10))
        channel1_label.setMinimumWidth(150)
        channel1_label.setStyleSheet("QLabel { color: #2c3e50; }")
        layout.addWidget(channel1_label, 0, 0)
        self.channel1_spinbox = QSpinBox()
        self.channel1_spinbox.setRange(0, LIMITS["MAX_COILS_PER_CHANNEL"])
        self.channel1_spinbox.setValue(0)
        self.channel1_spinbox.setMinimumWidth(100)
        layout.addWidget(self.channel1_spinbox, 0, 1)

        # Канал 2
        channel2_label = QLabel("Канал 2 (катушек):")
        channel2_label.setFont(QFont("Arial", 10))
        channel2_label.setMinimumWidth(150)
        channel2_label.setStyleSheet("QLabel { color: #2c3e50; }")
        layout.addWidget(channel2_label, 1, 0)
        self.channel2_spinbox = QSpinBox()
        self.channel2_spinbox.setRange(0, LIMITS["MAX_COILS_PER_CHANNEL"])
        self.channel2_spinbox.setValue(0)
        self.channel2_spinbox.setMinimumWidth(100)
        layout.addWidget(self.channel2_spinbox, 1, 1)

        return group

    def _create_modbus_group(self) -> QGroupBox:
        """Создать группу Modbus параметров"""
        group = QGroupBox("Modbus RTU")
        layout = QGridLayout(group)
        layout.setHorizontalSpacing(15)
        layout.setVerticalSpacing(10)

        # Скорость
        speed_label = QLabel("Скорость (baud):")
        speed_label.setFont(QFont("Arial", 10))
        speed_label.setMinimumWidth(150)
        speed_label.setStyleSheet("QLabel { color: #2c3e50; }")
        layout.addWidget(speed_label, 0, 0)
        self.modbus_speed_combo = QComboBox()
        self.modbus_speed_combo.setEditable(True)
        self.modbus_speed_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.modbus_speed_combo.setCurrentText("38400")
        self.modbus_speed_combo.setMinimumWidth(100)
        layout.addWidget(self.modbus_speed_combo, 0, 1)

        # Адрес
        addr_label = QLabel("Адрес устройства:")
        addr_label.setFont(QFont("Arial", 10))
        addr_label.setMinimumWidth(150)
        addr_label.setStyleSheet("QLabel { color: #2c3e50; }")
        layout.addWidget(addr_label, 1, 0)
        self.modbus_address_spinbox = QSpinBox()
        self.modbus_address_spinbox.setRange(LIMITS["MIN_DEVICE_ADDRESS"], LIMITS["MAX_DEVICE_ADDRESS"])
        self.modbus_address_spinbox.setValue(4)
        self.modbus_address_spinbox.setMinimumWidth(100)
        layout.addWidget(self.modbus_address_spinbox, 1, 1)

        return group

    def _create_can_group(self) -> QGroupBox:
        """Создать группу CAN параметров"""
        group = QGroupBox("CAN")
        layout = QGridLayout(group)
        layout.setHorizontalSpacing(15)
        layout.setVerticalSpacing(10)

        # Скорость
        speed_label = QLabel("Скорость:")
        speed_label.setFont(QFont("Arial", 10))
        speed_label.setMinimumWidth(150)
        speed_label.setStyleSheet("QLabel { color: #2c3e50; }")
        layout.addWidget(speed_label, 0, 0)
        self.can_speed_combo = QComboBox()
        self.can_speed_combo.setEditable(True)
        self.can_speed_combo.addItems(["10K", "20K", "50K", "125K", "250K", "500K", "800K", "1000K"])
        self.can_speed_combo.setCurrentText("1000K")
        self.can_speed_combo.setMinimumWidth(100)
        layout.addWidget(self.can_speed_combo, 0, 1)

        # Адрес
        addr_label = QLabel("Адрес:")
        addr_label.setFont(QFont("Arial", 10))
        addr_label.setMinimumWidth(150)
        addr_label.setStyleSheet("QLabel { color: #2c3e50; }")
        layout.addWidget(addr_label, 1, 0)
        self.can_address_combo = QComboBox()
        self.can_address_combo.setEditable(True)
        self.can_address_combo.addItems([str(i) for i in range(1, 11)])
        self.can_address_combo.setCurrentText("2")
        self.can_address_combo.setMinimumWidth(100)
        layout.addWidget(self.can_address_combo, 1, 1)

        return group

    def _create_firmware_group(self) -> QGroupBox:
        """Создать группу информации о прошивке"""
        from firmware_display import FirmwareDisplay
        
        self.firmware_display = FirmwareDisplay(self)
        return self.firmware_display.get_widget()

    def set_worker_thread(self, worker_thread):
        """Установить worker thread"""
        self.worker_thread = worker_thread
        
        # Создаём config manager
        from config_manager import ConfigManager
        self.config_manager = ConfigManager(worker_thread)
        
        # Разблокируем кнопку чтения
        self.read_btn.setEnabled(True)
        self.log_viewer.info("Worker thread установлен, доступно чтение конфигурации")

    def read_config(self):
        """Прочитать конфигурацию из устройства (асинхронно)"""
        if not self.worker_thread or not self.worker_thread.is_connected:
            self.log_viewer.fail("Соединение не установлено")
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к устройству")
            return

        # Блокируем кнопку и показываем прогресс
        self.read_btn.setEnabled(False)
        self.write_btn.setEnabled(False)
        # self.test_btn.setEnabled(False)
        self._set_operation_progress(True, "Чтение конфигурации...")
        
        # Временно останавливаем мониторинг подключения чтобы не было ложных срабатываний
        self._pause_connection_monitor()

        # Создаём и запускаем worker поток
        self.read_worker = ConfigReadWorker(self.config_manager, self.worker_thread)
        self.read_worker.setParent(self)  # Устанавливаем родителя чтобы не уничтожился
        self.read_worker.finished.connect(self._on_read_finished)
        self.read_worker.error.connect(self._on_read_error)
        self.read_worker.progress.connect(self._on_read_progress)
        self.read_worker.start()

    def set_main_window(self, main_window):
        """Установить ссылку на главное окно"""
        self.main_window = main_window
        
        # Подписываемся на сигнал отключения от step2
        if self.main_window and hasattr(self.main_window, 'step2'):
            self.main_window.step2.disconnected.connect(self._on_device_disconnected)
    
    def _on_device_disconnected(self):
        """Устройство отключено во время работы на шаге 3"""
        self.log_viewer.fail("❌ Устройство отключено!")
        
        # Блокируем кнопки
        self.read_btn.setEnabled(False)
        self.write_btn.setEnabled(False)
        
        # Скрываем прогресс если был
        self._set_operation_progress(False)
        
        # Останавливаем worker потоки если есть
        if self.read_worker and self.read_worker.isRunning():
            self.read_worker.wait()
            self.read_worker = None
        
        if self.write_worker and self.write_worker.isRunning():
            self.write_worker.wait()
            self.write_worker = None
        
        self.log_viewer.info("[CONFIG] Устройство отключено - ожидание перехода на шаг 2...")

    def _pause_connection_monitor(self):
        """Временно остановить мониторинг подключения"""
        if self.main_window and hasattr(self.main_window, 'step2'):
            self.main_window.step2._stop_connection_monitoring()
            self.log_viewer.info("[CONFIG] Мониторинг остановлен для операции")

    def _resume_connection_monitor(self):
        """Перезапустить мониторинг подключения после операции"""
        if self.main_window and hasattr(self.main_window, 'step2'):
            # Перезапускаем через 2 секунды чтобы операция завершилась
            QTimer.singleShot(2000, lambda: self.main_window.step2._start_connection_monitoring())
            self.log_viewer.info("[CONFIG] Мониторинг будет перезапущен через 2с")

    def _on_read_progress(self, status: str):
        """Обновление статуса чтения"""
        self.operation_status_label.setText(status)
        self.log_viewer.info(status)

    def _on_read_finished(self, config: dict):
        """Чтение завершено успешно"""
        # Скрываем прогресс
        self._set_operation_progress(False)
        
        # Логируем для отладки
        self.log_viewer.info(f"[DEBUG] Получена конфигурация: {config}")

        # Проверяем что конфигурация не пустая
        if not config or (config.get('channel1', 0) == 0 and config.get('channel2', 0) == 0):
            self.log_viewer.warning("Конфигурация пуста или содержит нулевые значения")
            # Всё равно используем то что есть

        self.config_data = config
        self.config_loaded = True

        # Обновляем UI
        self._update_ui_from_config(config)

        # Отображаем информацию о прошивке
        device_info = config.get('device_info')
        if device_info:
            baudrate = getattr(self.worker_thread, 'baudrate', 38400)
            self.firmware_display.display_firmware_info(device_info, baudrate)

        self.log_viewer.ok("Конфигурация успешно прочитана")

        # Отправляем сигнал о чтении (не о записи!)
        self.config_read.emit(config)

        # Перезапускаем мониторинг подключения
        self._resume_connection_monitor()

        # Разблокируем кнопки
        self.read_btn.setEnabled(True)
        self.write_btn.setEnabled(True)
        # self.test_btn.setEnabled(True)

    def _on_read_error(self, error: str):
        """Ошибка чтения"""
        # Скрываем прогресс
        self._set_operation_progress(False)
        
        # Перезапускаем мониторинг подключения
        self._resume_connection_monitor()

        self.log_viewer.fail(error)
        self.read_btn.setEnabled(True)
        self.write_btn.setEnabled(True)
        # self.test_btn.setEnabled(True)

    def _update_ui_from_config(self, config: dict):
        """Обновить UI из конфигурации"""
        if "channel1" in config:
            self.channel1_spinbox.setValue(config["channel1"])
        if "channel2" in config:
            self.channel2_spinbox.setValue(config["channel2"])
        if "modbus_speed_text" in config:
            self.modbus_speed_combo.setCurrentText(config["modbus_speed_text"])
        if "modbus_address" in config:
            self.modbus_address_spinbox.setValue(config["modbus_address"])
        if "can_speed_text" in config:
            self.can_speed_combo.setCurrentText(config["can_speed_text"])
        if "can_address" in config:
            self.can_address_combo.setCurrentText(str(config["can_address"]))

    def write_config(self):
        """Записать конфигурацию в устройство (асинхронно)"""
        if not self.config_loaded:
            self.log_viewer.warning("Сначала прочитайте конфигурацию")
            QMessageBox.warning(self, "Ошибка", "Сначала прочитайте конфигурацию")
            return

        if not self.worker_thread or not self.worker_thread.is_connected:
            self.log_viewer.fail("Соединение не установлено")
            QMessageBox.warning(self, "Ошибка", "Соединение не установлено")
            return

        # Получаем конфигурацию из UI
        config = self._get_config_from_ui()

        # Показываем диалог подтверждения
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы действительно хотите записать конфигурацию?\n\n"
            f"Канал 1: {config['channel1']} катушек\n"
            f"Канал 2: {config['channel2']} катушек\n"
            f"Modbus скорость: {config['modbus_speed_text']}\n"
            f"Modbus адрес: {config['modbus_address']}\n"
            f"CAN скорость: {config['can_speed_text']}\n"
            f"CAN адрес: {config['can_address']}\n\n"
            f"Это действие изменит настройки устройства.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Блокируем кнопку и показываем прогресс
        self.write_btn.setEnabled(False)
        self.read_btn.setEnabled(False)
        # self.test_btn.setEnabled(False)
        self._set_operation_progress(True, "Запись конфигурации...")
        
        # Временно останавливаем мониторинг подключения чтобы не было ложных срабатываний
        self._pause_connection_monitor()

        # Создаём и запускаем worker поток
        self.write_worker = ConfigWriteWorker(self.config_manager, config)
        self.write_worker.setParent(self)  # Устанавливаем родителя чтобы не уничтожился
        self.write_worker.finished.connect(self._on_write_finished)
        self.write_worker.error.connect(self._on_write_error)
        self.write_worker.progress.connect(self._on_write_progress)
        self.write_worker.start()

    def _on_write_progress(self, status: str):
        """Обновление статуса записи"""
        self.operation_status_label.setText(status)
        self.log_viewer.info(status)

    def _on_write_finished(self, success: bool):
        """Запись завершена успешно"""
        # Скрываем прогресс
        self._set_operation_progress(False)
        
        # Логируем для отладки
        self.log_viewer.info(f"[DEBUG] _on_write_finished вызван с success={success}")

        if success:
            self.log_viewer.ok("Конфигурация успешно записана")
            self.log_viewer.info("[DEBUG] Отправляем сигнал config_written.emit()")

            # Отправляем сигнал главному окну о необходимости перезагрузки
            self.config_written.emit()
            
            # Перезапускаем мониторинг СРАЗУ (не через 2 секунды)
            self._resume_connection_monitor_immediate()
        else:
            self.log_viewer.fail("Ошибка записи конфигурации")

        # Разблокируем кнопки
        self.write_btn.setEnabled(True)
        self.read_btn.setEnabled(True)
        # self.test_btn.setEnabled(True)

    def _resume_connection_monitor_immediate(self):
        """Перезапустить мониторинг подключения сразу после операции (БЫСТРЫЙ режим)"""
        if self.main_window and hasattr(self.main_window, 'step2'):
            # Запускаем БЫСТРЫЙ режим для обнаружения отключения питания
            self.main_window.step2._start_connection_monitoring(fast_mode=True)
            self.log_viewer.info("[CONFIG] Мониторинг перезапущен (БЫСТРЫЙ режим)")

    def _on_write_error(self, error: str):
        """Ошибка записи"""
        # Скрываем прогресс
        self._set_operation_progress(False)
        
        # Перезапускаем мониторинг подключения
        self._resume_connection_monitor()

        self.log_viewer.fail(error)
        self.write_btn.setEnabled(True)
        self.read_btn.setEnabled(True)
        # self.test_btn.setEnabled(True)

    def _get_config_from_ui(self) -> dict:
        """Получить конфигурацию из UI"""
        return {
            "channel1": self.channel1_spinbox.value(),
            "channel2": self.channel2_spinbox.value(),
            "modbus_speed_text": self.modbus_speed_combo.currentText(),
            "modbus_address": self.modbus_address_spinbox.value(),
            "can_speed_text": self.can_speed_combo.currentText(),
            "can_address": int(self.can_address_combo.currentText()),
        }

    def open_test_window(self):
        """Открыть окно тестирования"""
        if not self.config_loaded:
            self.log_viewer.warning("Сначала прочитайте конфигурацию")
            return

        if self.test_window is None or not self.test_window.isVisible():
            from .test_window import TestWindow
            self.test_window = TestWindow(self.worker_thread, self.config_data, self)
            self.test_window.exec_()  # Модальное окно
            self.test_window = None
        else:
            self.test_window.activateWindow()
            self.test_window.raise_()

        self.log_viewer.test("Окно тестирования открыто")

    def _set_operation_progress(self, visible: bool, status_text: str = ""):
        """Показать/скрыть прогресс бар операции"""
        self.progress_bar.setVisible(visible)
        self.operation_status_label.setVisible(visible)
        if visible and status_text:
            self.operation_status_label.setText(status_text)

    def reset(self):
        """Сбросить состояние шага"""
        self.config_loaded = False
        self.config_data = {}

        # Сбрасываем UI
        self.channel1_spinbox.setValue(0)
        self.channel2_spinbox.setValue(0)
        self.modbus_speed_combo.setCurrentText("38400")
        self.modbus_address_spinbox.setValue(4)
        self.can_speed_combo.setCurrentText("1000K")
        self.can_address_combo.setCurrentText("2")

        # Блокируем кнопки
        self.read_btn.setEnabled(False)
        self.write_btn.setEnabled(False)
        # self.test_btn.setEnabled(False)

        # Скрываем прогресс
        self._set_operation_progress(False)

        # Очищаем логи
        self.log_viewer.clear()

        # Очищаем прошивку
        self.firmware_display.clear_display()

        self.log_viewer.info("Шаг сброшен")

    def cleanup(self):
        """Очистка при уходе с шага"""
        # Останавливаем worker потоки если есть
        if self.read_worker and self.read_worker.isRunning():
            self.read_worker.wait()
            self.read_worker = None
        
        if self.write_worker and self.write_worker.isRunning():
            self.write_worker.wait()
            self.write_worker = None
        
        # Закрываем окно тестирования
        if self.test_window and self.test_window.isVisible():
            self.test_window.close()
            self.test_window = None
