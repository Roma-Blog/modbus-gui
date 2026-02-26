#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 2: Connect - Шаг подключения с автопоиском
"""

import sys
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QSpacerItem, QSizePolicy, QProgressBar
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .components.log_viewer import LogViewer
from .components.connection_status import ConnectionStatusIndicator
from .connection_monitor import ConnectionMonitor

# USB монитор доступен всегда (теперь кроссплатформенный)
from .usb_monitor import USBMonitor
_usb_monitor_available = True


class StepConnect(QWidget):
    """
    Шаг 2: Подключение

    Функции:
    - Выбор COM порта
    - Автопоиск устройства (адрес + скорость)
    - Отображение логов
    - Индикатор статуса
    - Кнопки Подключиться/Отключиться
    """

    # Сигналы для уведомления главного окна
    connected = pyqtSignal()
    disconnected = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Состояние
        self.is_connected = False
        self.is_connecting = False
        self.is_searching = False
        self.port = None
        self.address = None
        self.baudrate = None
        self.worker_thread = None
        self.auto_search_worker = None
        self.connection_monitor = None  # Монитор подключения (Modbus опрос)
        self.usb_monitor = None  # Системный USB монитор (udev)
        
        self.init_ui()
        self.scan_ports()

    def init_ui(self):
        """Инициализация UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # Заголовок
        title = QLabel("Подключение к устройству")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("QLabel { color: #2c3e50; }")
        layout.addWidget(title)

        # Выбор порта
        port_layout = QHBoxLayout()
        port_label = QLabel("Выберите COM порт:")
        port_label.setFont(QFont("Arial", 11))
        port_layout.addWidget(port_label)

        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        self.port_combo.setMinimumWidth(200)
        self.port_combo.setFont(QFont("Arial", 10))
        port_layout.addWidget(self.port_combo)

        # Кнопка обновления портов
        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.setFixedHeight(30)
        self.refresh_btn.setToolTip("Обновить список портов")
        self.refresh_btn.clicked.connect(self.scan_ports)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        port_layout.addWidget(self.refresh_btn)
        port_layout.addStretch()
        layout.addLayout(port_layout)

        # Индикатор статуса
        self.status_indicator = ConnectionStatusIndicator()
        layout.addWidget(self.status_indicator)

        # Прогресс бар поиска
        self.search_progress = QProgressBar()
        self.search_progress.setVisible(False)
        self.search_progress.setRange(0, 0)  # Непрерывная анимация
        layout.addWidget(self.search_progress)

        # Лог поиска
        self.search_status_label = QLabel("")
        self.search_status_label.setFont(QFont("Arial", 10))
        self.search_status_label.setStyleSheet("QLabel { color: #ff9800; font-style: italic; }")
        self.search_status_label.setVisible(False)
        layout.addWidget(self.search_status_label)

        # Логи
        self.log_viewer = LogViewer(title="Логи подключения")
        layout.addWidget(self.log_viewer)

        # Spacer
        spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.connect_btn = QPushButton("Подключиться")
        self.connect_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.connect_btn.setMinimumSize(150, 45)
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        btn_layout.addWidget(self.connect_btn)
        layout.addLayout(btn_layout)

    def scan_ports(self):
        """Сканировать доступные COM порты"""
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()

            self.port_combo.clear()
            available_ports = []

            for port in ports:
                port_name = port.device
                # Добавляем описание если доступно
                if port.description and port.description != "n/a":
                    port_name = f"{port.device} ({port.description})"
                available_ports.append(port_name)

            # Добавляем стандартные порты для текущей платформы
            from constants import DEFAULT_COM_PORTS
            for std_port in DEFAULT_COM_PORTS:
                if std_port not in available_ports:
                    available_ports.append(std_port)

            self.port_combo.addItems(available_ports)

            if available_ports:
                self.port_combo.setCurrentIndex(0)

            self.log_viewer.info(f"Найдено портов: {len(ports)}")
            for port in ports:
                self.log_viewer.debug(f"  - {port.device}: {port.description}")

        except ImportError:
            self.log_viewer.warning("Модуль pyserial не найден")
            # Используем стандартный список
            from constants import DEFAULT_COM_PORTS
            self.port_combo.clear()
            self.port_combo.addItems(DEFAULT_COM_PORTS)
        except Exception as e:
            self.log_viewer.fail(f"Ошибка сканирования портов: {e}")

    def toggle_connection(self):
        """Переключение подключения"""
        if self.is_connected:
            self.disconnect()
        elif self.is_searching:
            self.stop_search()
        else:
            self.connect()

    def connect(self):
        """Начать подключение с автопоиском"""
        port_text = self.port_combo.currentText()
        # Извлекаем только имя порта (без описания)
        self.port = port_text.split(" ")[0] if " " in port_text else port_text
        
        if not self.port:
            self.log_viewer.warning("Выберите COM порт")
            return
        
        self.log_viewer.auto(f"Запуск автопоиска на порту {self.port}...")
        self.is_searching = True
        self.is_connecting = True
        
        # Блокируем UI
        self.port_combo.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.connect_btn.setText("Отмена")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        # Показываем прогресс
        self.search_progress.setVisible(True)
        self.search_status_label.setVisible(True)
        self.search_status_label.setText("Инициализация сканера...")
        
        # Обновляем статус
        self.status_indicator.set_searching("Инициализация...")
        
        # Запускаем автопоиск
        self._start_auto_search()

    def _start_auto_search(self):
        """Запустить автопоиск устройства"""
        from auto_search_worker import AutoSearchWorker
        
        self.auto_search_worker = AutoSearchWorker(self.port, timeout_ms=100)
        self.auto_search_worker.device_found.connect(self._on_device_found)
        self.auto_search_worker.search_progress.connect(self._on_search_progress)
        self.auto_search_worker.search_complete.connect(self._on_search_complete)
        self.auto_search_worker.error_occurred.connect(self._on_search_error)
        self.auto_search_worker.start()
        
        self.log_viewer.auto("Rust сканер запущен - быстрый перебор адресов/скоростей")

    def _on_device_found(self, device_info: dict):
        """Устройство найдено"""
        self.address = device_info['address']
        self.baudrate = device_info['baudrate']
        
        self.log_viewer.ok(f"✓ Устройство найдено: адрес={self.address}, скорость={self.baudrate}")
        self.search_status_label.setText(
            f"✓ Найдено: адрес {self.address}, скорость {self.baudrate} baud"
        )

    def _on_search_progress(self, status: str):
        """Обновление прогресса поиска"""
        self.search_status_label.setText(status)
        self.log_viewer.auto(status)

    def _on_search_complete(self, success: bool, message: str):
        """Поиск завершён"""
        self.search_progress.setVisible(False)
        self.search_status_label.setVisible(False)
        self.is_searching = False
        self.is_connecting = False
        
        if success:
            self.log_viewer.ok(f"Автопоиск завершён: {message}")
            self._connect_to_device()
        else:
            self.log_viewer.fail(f"Автопоиск завершён: {message}")
            self._reset_ui()
            self.status_indicator.set_disconnected()

    def _on_search_error(self, error_message: str):
        """Ошибка автопоиска"""
        self.search_progress.setVisible(False)
        self.search_status_label.setVisible(False)
        self.is_searching = False
        self.is_connecting = False
        
        self.log_viewer.fail(f"Ошибка автопоиска: {error_message}")
        self._reset_ui()
        self.status_indicator.set_disconnected()

    def _connect_to_device(self):
        """Подключиться к найденному устройству"""
        from modbus_worker import ModbusWorkerThread
        
        self.log_viewer.info(f"Подключение к устройству ({self.port}, {self.address}, {self.baudrate})...")
        
        # Создаём worker thread
        self.worker_thread = ModbusWorkerThread(self.port, self.address, self.baudrate)
        self.worker_thread.connected.connect(self._on_connected)
        self.worker_thread.error_occurred.connect(self._on_error)
        self.worker_thread.status_updated.connect(self._on_status)
        self.worker_thread.start()
        
        # Ждём подключения
        QTimer.singleShot(5000, self._check_connection_timeout)

    def _check_connection_timeout(self):
        """Проверка таймаута подключения"""
        if self.is_connecting and self.worker_thread:
            self.log_viewer.warning("Таймаут подключения")
            self._reset_ui()

    def _on_connected(self, success: bool, message: str):
        """Результат подключения"""
        if success:
            self.is_connected = True
            self.is_connecting = False

            self.log_viewer.ok(f"Подключение успешно: {message}")
            self.status_indicator.set_connected(self.port, self.address, self.baudrate)

            # Обновляем кнопку
            self.connect_btn.setText("Отключиться")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)

            # Перезапускаем мониторинг подключения (после того как подключение установилось)
            QTimer.singleShot(2000, self._restart_connection_monitoring)

            # Сигнал о успешном подключении - активируем кнопку "Далее"
            self._notify_connected()
        else:
            self.log_viewer.fail(f"Ошибка подключения: {message}")
            self._reset_ui()

    def _restart_connection_monitoring(self):
        """Перезапустить мониторинг после подключения (обычный режим)"""
        if self.is_connected and not self.connection_monitor:
            self.log_viewer.info("[CONNECT] Запуск мониторинга подключения...")
            self._start_connection_monitoring(fast_mode=False)  # Обычный режим

    def _start_connection_monitoring(self, fast_mode=False):
        """Запустить мониторинг подключения
        
        Args:
            fast_mode: Быстрый режим (500мс) для обнаружения отключения после записи
        """
        # Сначала останавливаем старый мониторинг если есть
        self._stop_connection_monitoring()
        
        if self.worker_thread:
            interval = 500 if fast_mode else 3000  # 0.5с или 3с
            
            # Запускаем системный USB монитор (мгновенное обнаружение)
            if _usb_monitor_available and self.port:
                self.usb_monitor = USBMonitor(self.port)
                self.usb_monitor.device_removed.connect(self._on_usb_device_removed)
                self.usb_monitor.status_update.connect(self.log_viewer.info)
                self.usb_monitor.start()
                self.log_viewer.info(f"[USB] Системный мониторинг запущен")
            
            # Запускаем Modbus монитор (резервный)
            self.connection_monitor = ConnectionMonitor(
                self.worker_thread, 
                check_interval_ms=interval,
                fast_mode=fast_mode
            )
            self.connection_monitor.device_disconnected.connect(self._on_device_power_lost)
            self.connection_monitor.device_reconnected.connect(self._on_device_reconnected)
            self.connection_monitor.status_update.connect(self.log_viewer.info)
            self.connection_monitor.start()
            
            mode_text = "БЫСТРЫЙ" if fast_mode else "обычный"
            self.log_viewer.info(f"[MONITOR] Мониторинг запущен ({mode_text}, интервал {interval}мс)")

    def _on_usb_device_removed(self, device_path: str):
        """USB устройство отключено (системное событие) - МГНОВЕННОЕ ОБНАРУЖЕНИЕ"""
        self.log_viewer.fail(f"[USB] Устройство отключено: {device_path}")
        
        # Проверяем не ждём ли мы перезагрузку
        main_window = self.window()
        waiting_for_power_cycle = getattr(main_window, '_waiting_for_power_cycle', False)
        
        if waiting_for_power_cycle:
            self.log_viewer.info("[DEBUG] USB отключение после записи - закрываем уведомление и переходим на шаг 2")
            # Закрываем уведомление на шаге 3
            main_window._close_power_cycle_notification()
            # Переходим на шаг 2
            self._notify_disconnected()
        else:
            self.log_viewer.warning("[USB] Устройство отключено (не после записи)")
        
        # Останавливаем мониторинг
        self._stop_connection_monitoring()
        
        # Отключаемся через 100мс
        QTimer.singleShot(100, self.disconnect)

    def _on_device_reconnected(self):
        """Устройство снова подключено"""
        self.log_viewer.info("[MONITOR] Устройство снова доступно!")
        
        # Проверяем не ждём ли мы перезагрузку
        main_window = self.window()
        waiting_for_power_cycle = getattr(main_window, '_waiting_for_power_cycle', False)
        
        if waiting_for_power_cycle:
            # Устройство включили обратно - закрываем уведомление и остаёмся на шаге 3
            self.log_viewer.info("[DEBUG] Устройство включили - закрываем уведомление")
            main_window._close_power_cycle_notification()

    def _stop_connection_monitoring(self):
        """Остановить мониторинг подключения"""
        # Останавливаем USB монитор
        if self.usb_monitor:
            self.usb_monitor.stop()
            if not self.usb_monitor.wait(1000):
                self.log_viewer.warning("[USB] Таймаут остановки мониторинга")
            self.usb_monitor = None
            self.log_viewer.info(f"[USB] Системный мониторинг остановлен")
        
        # Останавливаем Modbus монитор
        if self.connection_monitor:
            self.connection_monitor.stop()
            # Ждём завершения потока чтобы избежать "Destroyed while still running"
            if not self.connection_monitor.wait(2000):  # Ждём до 2 секунд
                self.log_viewer.warning("[MONITOR] Таймаут остановки мониторинга")
            self.connection_monitor = None
            self.log_viewer.info(f"[MONITOR] Мониторинг остановлен")

    def _on_device_power_lost(self):
        """Устройство отключено от питания"""
        self.log_viewer.fail("[MONITOR] Устройство отключено от питания!")
        
        # Проверяем не ждём ли мы уже перезагрузку (чтобы не дублировать уведомления)
        main_window = self.window()
        waiting_for_power_cycle = getattr(main_window, '_waiting_for_power_cycle', False)
        
        self.log_viewer.info(f"[DEBUG] waiting_for_power_cycle={waiting_for_power_cycle}")
        
        if waiting_for_power_cycle:
            # Отправляем сигнал главному окну для перехода на шаг 2
            self.log_viewer.info("[DEBUG] Отправляем сигнал _notify_disconnected()")
            self._notify_disconnected()
        else:
            # Устройство отключили но не после записи - просто уведомляем
            self.log_viewer.info("[DEBUG] Отключение не после записи")
        
        # Останавливаем мониторинг чтобы не было повторных срабатываний
        self._stop_connection_monitoring()
        
        # Автоматически отключаемся через 500мс
        QTimer.singleShot(500, self.disconnect)

    def _notify_connected(self):
        """Уведомить родительское окно о подключении"""
        # Отправляем сигнал
        self.connected.emit()

    def _notify_disconnected(self):
        """Уведомить родительское окно об отключении"""
        # Отправляем сигнал
        self.disconnected.emit()

    def _on_error(self, error_message: str):
        """Ошибка"""
        self.log_viewer.fail(f"Ошибка: {error_message}")

    def _on_status(self, status_message: str):
        """Обновление статуса"""
        self.log_viewer.info(status_message)

    def disconnect(self):
        """Отключиться"""
        self.log_viewer.info("Отключение...")
        
        # Останавливаем монитор подключения
        self._stop_connection_monitoring()
        
        if self.worker_thread:
            self.worker_thread.stop()
            self.worker_thread.wait()
            self.worker_thread = None
        
        self.is_connected = False
        self.port = None
        self.address = None
        self.baudrate = None
        
        self._reset_ui()
        self.status_indicator.set_disconnected()

        # Сигнал об отключении
        self._notify_disconnected()

        self.log_viewer.ok("Отключено")

    def stop_search(self):
        """Остановить поиск"""
        self.log_viewer.info("Отмена поиска...")
        
        if self.auto_search_worker:
            self.auto_search_worker.stop()
            self.auto_search_worker.wait()
            self.auto_search_worker = None
        
        self.is_searching = False
        self.is_connecting = False
        
        self._reset_ui()
        self.search_progress.setVisible(False)
        self.search_status_label.setVisible(False)

    def _reset_ui(self):
        """Сброс UI"""
        self.port_combo.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.connect_btn.setText("Подключиться")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)

    def get_connection_data(self) -> dict:
        """Получить данные подключения"""
        return {
            'port': self.port,
            'address': self.address,
            'baudrate': self.baudrate,
            'worker_thread': self.worker_thread,
        }

    def cleanup(self):
        """Очистка при уходе с шага"""
        if self.is_searching:
            self.stop_search()
