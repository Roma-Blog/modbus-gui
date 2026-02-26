#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USB Monitor - Системный мониторинг USB устройств
Кроссплатформенное решение:
- Linux: pyudev (udev события)
- Windows: опрос через serial.tools.list_ports
"""

import sys
import os
import time

from PyQt5.QtCore import QThread, pyqtSignal

# Определяем платформу
IS_WINDOWS = sys.platform.startswith('win')
IS_LINUX = sys.platform.startswith('linux')

# Пытаемся импортировать pyudev для Linux
_pyudev_available = False
if IS_LINUX:
    try:
        import pyudev
        _pyudev_available = True
    except ImportError:
        pass


class USBMonitor(QThread):
    """
    Монитор USB устройств

    Кроссплатформенное решение:
    - Linux: использует pyudev для событий подключения/отключения
    - Windows: опрашивает список доступных портов
    """

    device_removed = pyqtSignal(str)  # Устройство отключено (путь устройства)
    device_added = pyqtSignal(str)    # Устройство подключено (путь устройства)
    status_update = pyqtSignal(str)   # Статус для логов

    def __init__(self, device_path: str = None, poll_interval_ms: int = 1000):
        """
        Инициализация монитора

        Args:
            device_path: Путь устройства (например, '/dev/ttyUSB0' или 'COM3')
            poll_interval_ms: Интервал опроса для Windows (мс)
        """
        super().__init__()
        self.device_path = device_path
        self.poll_interval_ms = poll_interval_ms
        self.should_stop = False
        self.context = None
        self.monitor = None
        self._known_ports = set()  # Для Windows: известные порты

        if not _pyudev_available and IS_LINUX:
            self.status_update.emit("[USB] pyudev не установлен - используйте fallback режим")
        elif IS_WINDOWS:
            self.status_update.emit("[USB] Windows: используется режим опроса портов")

    def run(self):
        """Основной цикл мониторинга"""
        if IS_WINDOWS:
            self._run_windows_mode()
        elif _pyudev_available:
            self._run_linux_udev_mode()
        else:
            self._run_linux_polling_mode()

    def _run_windows_mode(self):
        """Режим для Windows: опрос списка портов"""
        try:
            import serial.tools.list_ports
            
            # Инициализируем известный порт
            if self.device_path:
                self._known_ports.add(self.device_path)
            
            self.status_update.emit(f"[USB] Мониторинг запущен (Windows, опрос {self.poll_interval_ms}мс)")

            while not self.should_stop:
                self.msleep(self.poll_interval_ms)
                
                # Получаем текущие порты
                current_ports = set()
                for port in serial.tools.list_ports.comports():
                    current_ports.add(port.device)
                
                # Проверяем отключение
                for removed in self._known_ports - current_ports:
                    if self.device_path is None or removed == self.device_path:
                        self.status_update.emit(f"[USB] Устройство отключено: {removed}")
                        self.device_removed.emit(removed)
                
                # Проверяем подключение
                for added in current_ports - self._known_ports:
                    if self.device_path is None or added == self.device_path:
                        self.status_update.emit(f"[USB] Устройство подключено: {added}")
                        self.device_added.emit(added)
                
                # Обновляем известный список
                self._known_ports = current_ports

        except Exception as e:
            self.status_update.emit(f"[USB] Ошибка мониторинга (Windows): {e}")

    def _run_linux_udev_mode(self):
        """Режим для Linux: события udev (быстрое обнаружение)"""
        try:
            # Создаём контекст и монитор
            self.context = pyudev.Context()
            self.monitor = pyudev.Monitor.from_netlink(self.context)

            # Фильтруем только serial/tty устройства
            self.monitor.filter_by(subsystem='tty')

            # Включаем мониторинг
            self.monitor.enable_receiving()

            self.status_update.emit(f"[USB] Мониторинг запущен (Linux udev) для {self.device_path}")

            # Цикл обработки событий
            for device in iter(self.monitor.poll, None):
                if self.should_stop:
                    break

                device_node = device.device_node  # Например, '/dev/ttyUSB0'
                action = device.action  # 'add' или 'remove'

                # Если отслеживаем конкретное устройство
                if self.device_path and device_node != self.device_path:
                    continue

                if action == 'remove':
                    self.status_update.emit(f"[USB] Устройство отключено: {device_node}")
                    self.device_removed.emit(device_node)
                elif action == 'add':
                    self.status_update.emit(f"[USB] Устройство подключено: {device_node}")
                    self.device_added.emit(device_node)

        except Exception as e:
            self.status_update.emit(f"[USB] Ошибка мониторинга (Linux udev): {e}")

    def _run_linux_polling_mode(self):
        """Режим для Linux без pyudev: опрос списка портов"""
        try:
            import serial.tools.list_ports
            
            # Инициализируем известный порт
            if self.device_path:
                self._known_ports.add(self.device_path)
            
            self.status_update.emit(f"[USB] Мониторинг запущен (Linux polling, {self.poll_interval_ms}мс)")

            while not self.should_stop:
                self.msleep(self.poll_interval_ms)
                
                # Получаем текущие порты
                current_ports = set()
                for port in serial.tools.list_ports.comports():
                    current_ports.add(port.device)
                
                # Проверяем отключение
                for removed in self._known_ports - current_ports:
                    if self.device_path is None or removed == self.device_path:
                        self.status_update.emit(f"[USB] Устройство отключено: {removed}")
                        self.device_removed.emit(removed)
                
                # Проверяем подключение
                for added in current_ports - self._known_ports:
                    if self.device_path is None or added == self.device_path:
                        self.status_update.emit(f"[USB] Устройство подключено: {added}")
                        self.device_added.emit(added)
                
                # Обновляем известный список
                self._known_ports = current_ports

        except Exception as e:
            self.status_update.emit(f"[USB] Ошибка мониторинга (Linux polling): {e}")

    def stop(self):
        """Остановить мониторинг"""
        self.should_stop = True
