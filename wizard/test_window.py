#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Window - Отдельное окно тестирования устройства
"""

import sys
import os

from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QRadioButton, QButtonGroup, QGroupBox, QCheckBox,
    QFrame, QMessageBox, QProgressBar
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .components.log_viewer import LogViewer
from constants import TEST_MODES, COIL_ADDRESSES
from .test_worker import AsyncTestController


class TestWindow(QDialog):
    """
    Отдельное окно тестирования устройства (модальное)

    Функции:
    - Выбор режима тестирования
    - Автоматическое тестирование
    - Логирование операций
    - Управление тестами через TestController
    - Автоматическая остановка тестов при закрытии
    """

    def __init__(self, worker_thread, config_data: dict, parent=None):
        super().__init__(parent)

        self.worker_thread = worker_thread
        self.config_data = config_data

        # Состояние тестирования
        self.test_controller = None
        self.current_mode = TEST_MODES["FULL_SWITCH"]
        self.auto_testing = False
        self.test_running = False

        self.init_ui()
        self.setup_test_controller()

    def init_ui(self):
        """Инициализация UI"""
        self.setWindowTitle("Тестирование устройства")
        self.setMinimumSize(600, 500)
        self.resize(700, 600)
        
        # Устанавливаем модальность - блокируем родительское окно
        self.setModal(True)
        self.setParent(self.parent())

        # Устанавливаем layout напрямую (QDialog не имеет setCentralWidget)
        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(15)
        self.layout().setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel("Тестирование устройства")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("QLabel { color: #2c3e50; }")
        self.layout().addWidget(title)

        # Информация об устройстве
        info_label = QLabel(
            f"Канал 1: {self.config_data.get('channel1', 0)} катушек | "
            f"Канал 2: {self.config_data.get('channel2', 0)} катушек"
        )
        info_label.setFont(QFont("Arial", 10))
        info_label.setStyleSheet("QLabel { color: #7f8c8d; padding: 5px; background-color: #ecf0f1; border-radius: 4px; }")
        self.layout().addWidget(info_label)

        # Группа режимов тестирования
        mode_group = self._create_mode_group()
        self.layout().addWidget(mode_group)

        # Группа управления
        control_group = self._create_control_group()
        self.layout().addWidget(control_group)

        # Логи
        self.log_viewer = LogViewer(title="Логи тестирования")
        self.log_viewer.log_text.setMaximumHeight(200)
        self.layout().addWidget(self.log_viewer)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.start_btn = QPushButton("Старт")
        self.start_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.start_btn.setMinimumSize(120, 40)
        self.start_btn.clicked.connect(self.start_test)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Стоп")
        self.stop_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.stop_btn.setMinimumSize(120, 40)
        self.stop_btn.clicked.connect(self.stop_test)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        btn_layout.addWidget(self.stop_btn)

        btn_layout.addStretch()

        self.close_btn = QPushButton("Закрыть")
        self.close_btn.setFont(QFont("Arial", 11))
        self.close_btn.setMinimumSize(100, 40)
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_layout.addWidget(self.close_btn)

        self.layout().addLayout(btn_layout)

    def _create_mode_group(self) -> QGroupBox:
        """Создать группу выбора режима тестирования"""
        group = QGroupBox("Режим тестирования")
        layout = QVBoxLayout(group)

        # Радио-кнопки
        self.running_lights_radio = QRadioButton("Бегущие огни")
        self.running_lights_radio.setFont(QFont("Arial", 11))
        self.running_lights_radio.setToolTip(
            "Последовательное включение 3 соседних катушек\n"
            "Минимум 3 катушки на канал"
        )
        self.running_lights_radio.clicked.connect(self._on_mode_changed)
        layout.addWidget(self.running_lights_radio)

        self.full_switch_radio = QRadioButton("Полное переключение")
        self.full_switch_radio.setFont(QFont("Arial", 11))
        self.full_switch_radio.setChecked(True)
        self.full_switch_radio.setToolTip(
            "Включение/выключение всех катушек одновременно\n"
            "Одно нажатие - все ON, второе - все OFF"
        )
        self.full_switch_radio.clicked.connect(self._on_mode_changed)
        layout.addWidget(self.full_switch_radio)

        self.snake_radio = QRadioButton("Змейка")
        self.snake_radio.setFont(QFont("Arial", 11))
        self.snake_radio.setToolTip(
            "Последовательное включение всех катушек\n"
            "От первой к последней, затем сброс"
        )
        self.snake_radio.clicked.connect(self._on_mode_changed)
        layout.addWidget(self.snake_radio)

        # Группа кнопок
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.running_lights_radio, 0)
        self.button_group.addButton(self.full_switch_radio, 1)
        self.button_group.addButton(self.snake_radio, 2)

        return group

    def _create_control_group(self) -> QGroupBox:
        """Создать группу управления тестом"""
        group = QGroupBox("Управление")
        layout = QVBoxLayout(group)

        # Чекбокс автоматического тестирования
        self.auto_test_checkbox = QCheckBox("Автоматическое тестирование")
        self.auto_test_checkbox.setFont(QFont("Arial", 11))
        self.auto_test_checkbox.stateChanged.connect(self._on_auto_test_changed)
        self.auto_test_checkbox.setToolTip(
            "Автоматический запуск тестов с интервалом 500мс"
        )
        layout.addWidget(self.auto_test_checkbox)

        # Статус
        self.status_label = QLabel("Статус: Готов к тесту")
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setStyleSheet("QLabel { color: #27ae60; font-weight: bold; }")
        layout.addWidget(self.status_label)

        return group

    def setup_test_controller(self):
        """Настроить контроллер тестирования"""
        self.test_controller = AsyncTestController(
            self.worker_thread,
            log_callback=self._log
        )

        # Устанавливаем значения каналов
        channel1 = self.config_data.get('channel1', 0)
        channel2 = self.config_data.get('channel2', 0)
        self.test_controller.set_channel_values(channel1, channel2)

        self._log("Контроллер тестирования инициализирован")

    def _on_mode_changed(self):
        """Изменение режима тестирования"""
        self.test_controller.stop_all_tests()
        
        if self.running_lights_radio.isChecked():
            self.current_mode = TEST_MODES["RUNNING_LIGHTS"]
            self._log("Режим: Бегущие огни")
        elif self.full_switch_radio.isChecked():
            self.current_mode = TEST_MODES["FULL_SWITCH"]
            self._log("Режим: Полное переключение")
        elif self.snake_radio.isChecked():
            self.current_mode = TEST_MODES["SNAKE"]
            self._log("Режим: Змейка")

    def _on_auto_test_changed(self, state):
        """Изменение режима автоматического тестирования"""
        if state == Qt.Checked:
            self.auto_testing = True
            self._log("Автоматическое тестирование включено (после нажатия Старт)")
        else:
            self.auto_testing = False
            self._log("Автоматическое тестирование выключено")

    def start_test(self):
        """Запустить тест"""
        if not self.worker_thread or not self.worker_thread.is_connected:
            QMessageBox.warning(self, "Ошибка", "Соединение не установлено")
            return

        self.test_running = True
        self._log(f"Запуск теста: {self.current_mode}")
        self.status_label.setText("Статус: Тест выполняется")
        self.status_label.setStyleSheet("QLabel { color: #e67e22; font-weight: bold; }")

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.auto_test_checkbox.setEnabled(False)

        # Запускаем тест (с флагом auto если включен чекбокс)
        auto = self.auto_test_checkbox.isChecked()
        self.test_controller.run_test(mode=self.current_mode, auto=auto)

    def stop_test(self):
        """Остановить тест"""
        self._log("Остановка теста")
        self.test_controller.stop_all_tests()

        self.status_label.setText("Статус: Тест остановлен")
        self.status_label.setStyleSheet("QLabel { color: #e74c3c; font-weight: bold; }")

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.auto_test_checkbox.setEnabled(True)
        self.auto_testing = False
        self.auto_test_checkbox.setChecked(False)
        self.test_running = False

    def _log(self, message: str):
        """Добавить сообщение в лог"""
        self.log_viewer.test(message)

    def closeEvent(self, event):
        """Обработка закрытия окна - автоматически останавливаем тесты"""
        self._log("Закрытие окна тестирования...")
        
        # Останавливаем все тесты
        if self.test_controller:
            self.test_controller.stop_all_tests()
        
        self.test_running = False
        self._log("Окно тестирования закрыто")
        event.accept()

    def cleanup(self):
        """Очистка"""
        self._log("Очистка окна тестирования...")
        if self.test_controller:
            self.test_controller.stop_all_tests()
        self.test_running = False
