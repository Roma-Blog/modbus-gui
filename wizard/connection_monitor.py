#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Connection Monitor - Монитор подключения устройства
Отслеживает доступность устройства и сигнализирует об отключении
"""

import sys
import os

from PyQt5.QtCore import QThread, pyqtSignal

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ConnectionMonitor(QThread):
    """
    Монитор подключения устройства

    Периодически опрашивает устройство и сигнализирует когда оно перестаёт отвечать
    """

    device_disconnected = pyqtSignal()  # Устройство отключено
    device_reconnected = pyqtSignal()   # Устройство подключено снова
    status_update = pyqtSignal(str)     # Статус для логов

    def __init__(self, worker_thread, check_interval_ms=500, fast_mode=False):
        super().__init__()
        self.worker_thread = worker_thread
        self.check_interval_ms = check_interval_ms
        self.fast_mode = fast_mode  # Быстрый режим для обнаружения отключения
        self.should_stop = False
        self.is_connected = True
        self.consecutive_failures = 0
        self.max_failures = 2 if fast_mode else 3  # 2×0.5с=1с или 3×0.5с=1.5с

    def run(self):
        """Основной цикл мониторинга"""
        self.consecutive_failures = 0

        while not self.should_stop:
            self.msleep(self.check_interval_ms)

            if not self.worker_thread or not self.worker_thread.is_connected:
                self.consecutive_failures += 1
                if self.consecutive_failures >= self.max_failures:
                    if self.is_connected:
                        self.is_connected = False
                        self.device_disconnected.emit()
                continue

            # Пытаемся прочитать информацию об устройстве
            try:
                device_info = self.worker_thread.read_device_info()

                if device_info:
                    # Устройство отвечает
                    if not self.is_connected:
                        self.is_connected = True
                        self.consecutive_failures = 0
                        self.device_reconnected.emit()
                    else:
                        # Устройство уже было подключено - просто сбрасываем счётчик
                        self.consecutive_failures = 0
                else:
                    # Устройство не отвечает
                    self.consecutive_failures += 1
                    if self.consecutive_failures >= self.max_failures:
                        self.is_connected = False
                        self.device_disconnected.emit()

            except Exception as e:
                self.consecutive_failures += 1
                if self.consecutive_failures >= self.max_failures:
                    if self.is_connected:
                        self.is_connected = False
                        self.device_disconnected.emit()

        # Корректное завершение потока
        self.deleteLater()

    def stop(self):
        """Остановить мониторинг"""
        self.should_stop = True
