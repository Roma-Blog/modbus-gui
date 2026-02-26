#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wizard Main Window - Главное окно пошагового мастера
"""

import sys
import os

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QFrame, QLabel, QProgressBar,
    QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .step_welcome import StepWelcome
from .step_connect import StepConnect
from .step_config import StepConfig


class ConnectionWizard(QMainWindow):
    """
    Главное окно пошагового мастера подключения
    
    Шаги:
    1. Приветствие
    2. Подключение (автопоиск)
    3. Конфигурация
    """

    def __init__(self):
        super().__init__()

        # Состояние
        self.current_step = 0
        self.total_steps = 3
        self.connection_data = {}
        
        # Таймер для проверки отключения питания
        self._check_power_cycle_timer = None
        
        # Флаг ожидания перезагрузки после записи конфигурации
        self._waiting_for_power_cycle = False
        self._power_cycle_msg = None  # Ссылка на уведомление о перезагрузке
        self._power_cycle_timeout_timer = None  # Таймаут ожидания отключения

        self.init_ui()
        self.setup_steps()

    def init_ui(self):
        """Инициализация UI"""
        self.setWindowTitle("DVLINK GUI - Мастер подключения")
        self.setMinimumSize(900, 700)
        self.resize(1000, 750)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Заголовок с прогрессом
        header = self._create_header()
        layout.addWidget(header)

        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.total_steps - 1)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
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

        # Стек шагов
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background-color: white; }")
        layout.addWidget(self.stack)

        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("QFrame { background-color: #bdc3c7; }")
        layout.addWidget(line)

        # Кнопки навигации
        nav = self._create_navigation()
        layout.addWidget(nav)

    def _create_header(self) -> QWidget:
        """Создать заголовок"""
        header = QWidget()
        header.setFixedHeight(70)
        header.setStyleSheet("QWidget { background-color: #2c3e50; }")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)

        # Заголовок
        title = QLabel("DVLINK GUI")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("QLabel { color: white; }")
        layout.addWidget(title)

        # Индикатор шага
        self.step_label = QLabel("Шаг 1 из 3: Приветствие")
        self.step_label.setFont(QFont("Arial", 12))
        self.step_label.setStyleSheet("QLabel { color: #bdc3c7; }")
        layout.addWidget(self.step_label)

        layout.addStretch()

        return header

    def _create_navigation(self) -> QWidget:
        """Создать навигацию"""
        nav = QWidget()
        nav.setFixedHeight(70)
        nav.setStyleSheet("QWidget { background-color: #f8f9fa; }")

        layout = QHBoxLayout(nav)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        # Кнопка "Назад"
        self.back_btn = QPushButton("← Назад")
        self.back_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.back_btn.setMinimumSize(120, 40)
        self.back_btn.clicked.connect(self.prev_step)
        self.back_btn.setEnabled(False)
        self.back_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        layout.addWidget(self.back_btn)

        layout.addStretch()

        # Кнопка "Далее"
        self.next_btn = QPushButton("Далее →")
        self.next_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.next_btn.setMinimumSize(120, 40)
        self.next_btn.clicked.connect(self.next_step)
        self.next_btn.setStyleSheet("""
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
        layout.addWidget(self.next_btn)

        # Кнопка "Готово"
        self.finish_btn = QPushButton("✓ Готово")
        self.finish_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.finish_btn.setMinimumSize(120, 40)
        self.finish_btn.clicked.connect(self.finish_wizard)
        self.finish_btn.setVisible(False)
        self.finish_btn.setStyleSheet("""
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
        layout.addWidget(self.finish_btn)

        return nav

    def setup_steps(self):
        """Настроить шаги"""
        # Шаг 1: Приветствие
        self.step1 = StepWelcome()
        self.stack.addWidget(self.step1)

        # Шаг 2: Подключение
        self.step2 = StepConnect()
        self.stack.addWidget(self.step2)
        # Подключаем сигналы
        self.step2.connected.connect(self.on_step2_connected)
        self.step2.disconnected.connect(self.on_step2_disconnected)

        # Шаг 3: Конфигурация
        self.step3 = StepConfig()
        self.step3.set_main_window(self)  # Устанавливаем ссылку на главное окно
        self.stack.addWidget(self.step3)
        # Подключаем сигнал ТОЛЬКО о записи конфигурации (не о чтении!)
        self.step3.config_written.connect(self.on_config_written)

        # Обновляем заголовок
        self._update_step_label()

    def _update_step_label(self):
        """Обновить индикатор шага"""
        step_names = [
            "Приветствие",
            "Подключение",
            "Конфигурация"
        ]
        self.step_label.setText(
            f"Шаг {self.current_step + 1} из {self.total_steps}: {step_names[self.current_step]}"
        )
        self.progress_bar.setValue(self.current_step)

    def next_step(self):
        """Перейти к следующему шагу"""
        if self.current_step < self.total_steps - 1:
            # Сохраняем данные перед переходом
            if self.current_step == 1:  # Переход с шага подключения
                self.connection_data = self.step2.get_connection_data()
                
                # Передаём worker thread на шаг конфигурации
                if self.connection_data.get('worker_thread'):
                    self.step3.set_worker_thread(self.connection_data['worker_thread'])
            
            self.current_step += 1
            self.stack.setCurrentIndex(self.current_step)
            self._update_step_label()
            self._update_buttons()

    def prev_step(self):
        """Вернуться к предыдущему шагу"""
        if self.current_step > 0:
            # Очищаем предыдущий шаг
            if self.current_step == 2:  # Возврат с шага конфигурации
                self.step3.reset()
            
            if self.current_step == 1:  # Возврат на шаг подключения
                # Отключаемся при возврате на шаг 2
                if self.step2.is_connected:
                    self.step2.disconnect()
                    
                    # Показываем уведомление что можно подключить снова
                    QMessageBox.information(
                        self,
                        "Подключение",
                        "Вы вернулись на шаг подключения.\n\n"
                        "Если вы записали новые настройки адреса:\n"
                        "1. Убедитесь что устройство перезагружено\n"
                        "2. Выберите порт и нажмите 'Подключиться'\n"
                        "3. Автопоиск найдёт устройство на новом адресе"
                    )
            
            self.current_step -= 1
            self.stack.setCurrentIndex(self.current_step)
            self._update_step_label()
            self._update_buttons()

    def _update_buttons(self):
        """Обновить состояние кнопок"""
        # Кнопка "Назад"
        self.back_btn.setEnabled(self.current_step > 0)

        # Кнопка "Далее"
        if self.current_step == 0:
            self.next_btn.setEnabled(True)
            self.next_btn.setVisible(True)
            self.finish_btn.setVisible(False)
        elif self.current_step == 1:
            # На шаге подключения - только если подключено
            self.next_btn.setEnabled(self.step2.is_connected)
            self.next_btn.setVisible(True)
            self.finish_btn.setVisible(False)
        elif self.current_step == 2:
            # На шаге конфигурации - скрываем "Далее" и "Готово"
            # (пользователь должен работать с конфигурацией, а не завершать мастер)
            self.next_btn.setVisible(False)
            self.finish_btn.setVisible(False)

    def finish_wizard(self):
        """Завершить мастер"""
        # Просто закрываем окно - все данные сохранены
        self.close()

    def on_step2_connected(self):
        """Обработчик подключения на шаге 2"""
        # Разблокируем кнопку "Далее"
        self.next_btn.setEnabled(True)

    def on_step2_disconnected(self):
        """Обработчик отключения на шаге 2"""
        self.log_message("[DEBUG] on_step2_disconnected вызван!")

        # Блокируем кнопку "Далее"
        self.next_btn.setEnabled(False)

        # Если устройство отключено после записи конфигурации - переходим на шаг 2
        if self.current_step == 2 and self._waiting_for_power_cycle:
            self.log_message("[DEBUG] Переход на шаг 2 после отключения питания")

            # Сбрасываем флаг
            self._waiting_for_power_cycle = False

            # Останавливаем таймаут
            if self._power_cycle_timeout_timer:
                self._power_cycle_timeout_timer.stop()
                self._power_cycle_timeout_timer = None

            # Закрываем старое уведомление о перезагрузке
            if hasattr(self, '_power_cycle_msg') and self._power_cycle_msg:
                self._power_cycle_msg.close()
                self._power_cycle_msg = None

            # Сбрасываем состояние шага 3 (конфигурация)
            self.step3.reset()

            # Переходим на шаг подключения
            self.current_step = 1
            self.stack.setCurrentIndex(1)
            self._update_step_label()
            self._update_buttons()

            # Показываем уведомление что можно включать
            QTimer.singleShot(500, lambda: QMessageBox.information(
                self,
                "МОЖНО ВКЛЮЧАТЬ ПИТАНИЕ",
                "Устройство готово:\n\n"
                "1. ВКЛЮЧИТЕ ПИТАНИЕ УСТРОЙСТВА\n\n"
                "2. ДОЖДИТЕСЬ ПОЛНОГО ЗАГОРАНИЯ ВСЕХ СВЕТОДИОДОВ\n\n"
                "3. НАЖМИТЕ «ПОДКЛЮЧИТЬСЯ»\n\n"
                "После подключения проверьте что новая\n"
                "конфигурация применилась."
            ))
        elif self.current_step == 2 and not self._waiting_for_power_cycle:
            # Отключение на шаге 3 (не после записи) - неожиданное отключение
            self.log_message("[DEBUG] Неожиданное отключение на шаге 3")

            # Сбрасываем флаг если был
            if self._waiting_for_power_cycle:
                self._waiting_for_power_cycle = False

                # Останавливаем таймаут
                if self._power_cycle_timeout_timer:
                    self._power_cycle_timeout_timer.stop()
                    self._power_cycle_timeout_timer = None

                # Закрываем уведомление
                if hasattr(self, '_power_cycle_msg') and self._power_cycle_msg:
                    self._power_cycle_msg.close()
                    self._power_cycle_msg = None

            # Сбрасываем состояние шага 3
            self.step3.reset()

            # Переходим на шаг 2
            self.current_step = 1
            self.stack.setCurrentIndex(1)
            self._update_step_label()
            self._update_buttons()

            # Показываем уведомление о проблеме подключения
            QTimer.singleShot(300, lambda: QMessageBox.warning(
                self,
                "⚠️ Соединение потеряно",
                "Устройство неожиданно отключилось!\n"
                "Возможные причины:\n"
                "1. USB кабель отсоединён от ПК или устройства\n"
                "2. Плохой контакт в разъёме USB"
            ))
        elif self._waiting_for_power_cycle:
            # Устройство отключили но мы ещё на шаге 3 - закрываем уведомление
            self.log_message("[DEBUG] Устройство отключено, закрываем уведомление")

            # Сбрасываем флаг
            self._waiting_for_power_cycle = False

            # Останавливаем таймаут
            if self._power_cycle_timeout_timer:
                self._power_cycle_timeout_timer.stop()
                self._power_cycle_timeout_timer = None

            # Закрываем уведомление
            if hasattr(self, '_power_cycle_msg') and self._power_cycle_msg:
                self._power_cycle_msg.close()
                self._power_cycle_msg = None

    def log_message(self, message: str):
        """Добавить сообщение в лог (через step2)"""
        if hasattr(self.step2, 'log_viewer'):
            self.step2.log_viewer.info(message)

    def on_config_written(self):
        """Конфигурация записана - показать уведомление о перезагрузке"""
        # Логируем для отладки
        self.log_message("[DEBUG] on_config_written вызван!")
        
        # Устанавливаем флаг что ждём перезагрузку
        self._waiting_for_power_cycle = True
        
        # Запускаем таймаут - если не отключат за 60 секунд, закрываем уведомление
        self._power_cycle_timeout_timer = QTimer()
        self._power_cycle_timeout_timer.timeout.connect(self._on_power_cycle_timeout)
        self._power_cycle_timeout_timer.setSingleShot(True)
        self._power_cycle_timeout_timer.start(60000)  # 60 секунд
        
        # Показываем НЕПРЕРЫВАЕМОЕ уведомление (без кнопки)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Отключите питание")
        msg.setText("Конфигурация записана!")
        msg.setInformativeText(
            "ОТКЛЮЧИТЕ ПИТАНИЕ УСТРОЙСТВА\n\n"
            "И ждите когда это окно закроется автоматически...\n\n"
            "После отключения питания вы автоматически\n"
            "перейдёте на шаг подключения."
        )
        msg.setStandardButtons(QMessageBox.NoButton)  # НЕТ КНОПКИ - нельзя закрыть!
        
        # Показываем уведомление
        msg.show()
        msg.raise_()
        msg.activateWindow()
        
        # Сохраняем ссылку на уведомление чтобы закрыть позже
        self._power_cycle_msg = msg
        
        # Ждём отключения питания
        self.log_message("Ожидание отключения питания устройства...")

    def _on_power_cycle_timeout(self):
        """Таймаут ожидания отключения питания"""
        if self._waiting_for_power_cycle:
            self.log_message("[DEBUG] Таймаут ожидания отключения - закрываем уведомление")
            
            # Сбрасываем флаг
            self._waiting_for_power_cycle = False
            
            # Закрываем уведомление
            if hasattr(self, '_power_cycle_msg') and self._power_cycle_msg:
                self._power_cycle_msg.close()
                self._power_cycle_msg = None
            
            # Показываем уведомление что всё ок
            QMessageBox.information(
                self,
                "Перезагрузка не требуется",
                "Устройство не было отключено.\n\n"
                "Если конфигурация записана успешно,\n"
                "новые настройки применятся после\n"
                "следующей перезагрузки устройства."
            )

    def _close_power_cycle_notification(self):
        """Закрыть уведомление о перезагрузке (устройство отключено)"""
        if self._waiting_for_power_cycle:
            self.log_message("[DEBUG] Устройство отключено - закрываем уведомление")
            
            # Сбрасываем флаг
            self._waiting_for_power_cycle = False
            
            # Останавливаем таймаут
            if self._power_cycle_timeout_timer:
                self._power_cycle_timeout_timer.stop()
                self._power_cycle_timeout_timer = None
            
            # Закрываем уведомление
            if hasattr(self, '_power_cycle_msg') and self._power_cycle_msg:
                self._power_cycle_msg.close()
                self._power_cycle_msg = None
            
            self.log_message("Уведомление закрыто автоматически")

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        # Отключаем устройство если подключено
        if self.step2.is_connected:
            self.step2.disconnect()
        
        # Останавливаем таймер проверки питания
        if self._check_power_cycle_timer:
            self._check_power_cycle_timer.stop()
            self._check_power_cycle_timer = None
        
        # Останавливаем таймаут ожидания отключения
        if self._power_cycle_timeout_timer:
            self._power_cycle_timeout_timer.stop()
            self._power_cycle_timeout_timer = None

        # Очищаем ресурсы
        self.step2.cleanup()
        self.step3.cleanup()

        # Останавливаем worker thread если есть
        if self.connection_data.get('worker_thread'):
            worker = self.connection_data['worker_thread']
            if worker.isRunning():
                worker.stop()
                worker.wait()

        event.accept()
