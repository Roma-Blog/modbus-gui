#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Search Worker Module
Поток для автоматического поиска устройств Modbus RTU

Использует Rust сканер для быстрого перебора адресов и скоростей.
Алгоритм: для каждого адреса перебираем все скорости, затем переходим к следующему адресу.
"""

import sys
import os
from typing import Optional, Tuple, List, Dict, Any

from PyQt5.QtCore import QThread, pyqtSignal

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modbus_scanner_wrapper import ModbusScannerRust, DEFAULT_BAUDRATES as SCANNER_BAUDRATES


class AutoSearchWorker(QThread):
    """
    Поток для автоматического поиска устройства Modbus RTU
    
    Перебирает адреса и скорости в следующем порядке:
    - Адрес 1: все скорости (115200, 57600, 38400, 19200, 9600)
    - Адрес 2: все скорости
    - ...
    - Адрес N: все скорости
    
    Останавливается при первом найденном устройстве.
    """

    # Сигналы
    device_found = pyqtSignal(dict)  # device_info = {'address': int, 'baudrate': int, 'device_info': dict}
    search_progress = pyqtSignal(str)  # Текст статуса
    search_complete = pyqtSignal(bool, str)  # (success, message)
    error_occurred = pyqtSignal(str)

    # Стандартные скорости для перебора (как в test_rust_scanner.py)
    SEARCH_BAUDRATES = [115200, 57600, 38400, 19200, 9600]
    
    # Диапазон адресов для поиска
    MIN_ADDRESS = 1
    MAX_ADDRESS = 200

    def __init__(self, port: str, timeout_ms: int = 100):
        """
        Инициализация работника автопоиска

        Args:
            port: COM порт для сканирования
            timeout_ms: Таймаут операции в миллисекундах
        """
        super().__init__()
        self.port = port
        self.timeout_ms = timeout_ms
        self.should_stop = False
        self.scanner = None
        self._found_device = None

    def run(self):
        """Основной цикл поиска устройства"""
        try:
            self.search_progress.emit(f"Инициализация сканера на порту {self.port}...")

            # Инициализируем Rust сканер
            self.scanner = ModbusScannerRust(self.port, timeout_ms=self.timeout_ms)

            if not self.scanner._scanner:
                self.error_occurred.emit(
                    "Rust сканер не загружен. Установите: cd modbus_scanner_rust && maturin develop --release"
                )
                self.search_complete.emit(False, "Rust сканер недоступен")
                return

            self.search_progress.emit("Rust сканер готов. Начинаем поиск устройства...")

            # Запускаем поиск с правильным порядком: адрес -> все скорости -> следующий адрес
            self._sequential_search()

        except Exception as e:
            self.error_occurred.emit(f"Ошибка автопоиска: {str(e)}")
            self.search_complete.emit(False, f"Ошибка: {str(e)}")

    def _sequential_search(self):
        """
        Последовательный поиск: для каждого адреса перебираем все скорости
        
        Порядок:
        - Адрес 1: 115200, 57600, 38400, 19200, 9600
        - Адрес 2: 115200, 57600, 38400, 19200, 9600
        - ...
        """
        for address in range(self.MIN_ADDRESS, self.MAX_ADDRESS + 1):
            if self.should_stop:
                self.search_complete.emit(False, "Поиск остановлен пользователем")
                return

            self.search_progress.emit(f"Проверка адреса {address}/{self.MAX_ADDRESS}...")

            # Перебираем все скорости для текущего адреса
            for baudrate in self.SEARCH_BAUDRATES:
                if self.should_stop:
                    self.search_complete.emit(False, "Поиск остановлен пользователем")
                    return

                # Сканируем один адрес на одной скорости
                result = self.scanner.scan_single(
                    address=address,
                    baudrate=baudrate,
                    status_callback=lambda s: None  # Не спамим статусами
                )

                if result:
                    # Устройство найдено!
                    self.search_progress.emit(
                        f"✓ Устройство найдено: адрес {address}, скорость {baudrate} baud"
                    )
                    
                    # Получаем полную информацию об устройстве через команду 17
                    device_info = self._read_device_info(address, baudrate)
                    
                    self._found_device = {
                        'address': address,
                        'baudrate': baudrate,
                        'device_info': device_info
                    }
                    
                    # Отправляем сигнал о находке
                    self.device_found.emit(self._found_device)
                    self.search_complete.emit(True, f"Устройство найдено: адрес {address}, скорость {baudrate} baud")
                    return

            # Переходим к следующему адресу

        # Если дошли сюда - устройство не найдено
        self.search_complete.emit(False, "Устройство не найдено в диапазоне адресов 1-200")

    def _read_device_info(self, address: int, baudrate: int) -> Optional[Dict[str, Any]]:
        """
        Читает информацию об устройстве через команду 17
        
        Args:
            address: Адрес устройства
            baudrate: Скорость соединения
            
        Returns:
            Информация об устройстве или None
        """
        try:
            from core.modbus_rtu_client import ModbusRTUClient
            from core.device_response_parser_fixed import parse_specific_device_response

            # Создаем клиент для чтения информации
            client = ModbusRTUClient(self.port, address, baudrate)
            success, _ = client.connect()

            if success:
                raw_info = client.get_device_info()
                if raw_info:
                    # Парсим ответ
                    hex_response = raw_info.get('raw_response') or raw_info.get('hex_format')
                    if hex_response:
                        parsed_info = parse_specific_device_response(hex_response)
                        combined_info = {**raw_info, **parsed_info}
                    else:
                        combined_info = raw_info
                    
                    client.disconnect()
                    return combined_info
                
                client.disconnect()
            
            return None

        except Exception as e:
            self.search_progress.emit(f"Предупреждение: не удалось прочитать device_info: {e}")
            return None

    def stop(self):
        """Остановить поиск"""
        self.should_stop = True

    def stop_and_wait(self):
        """Остановить поиск и дождаться завершения потока"""
        self.stop()
        if self.isRunning():
            self.wait(3000)  # Ждем до 3 секунд


def quick_auto_search(port: str, timeout_ms: int = 100) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Быстрая функция для автоматического поиска устройства (синхронная версия)
    
    Args:
        port: COM порт
        timeout_ms: Таймаут операции
        
    Returns:
        (device_info, message) или (None, message) при неудаче
    """
    scanner = ModbusScannerRust(port, timeout_ms=timeout_ms)
    
    if not scanner._scanner:
        return None, "Rust сканер недоступен"
    
    for address in range(1, 201):
        for baudrate in [115200, 57600, 38400, 19200, 9600]:
            result = scanner.scan_single(address=address, baudrate=baudrate)
            if result:
                return {
                    'address': address,
                    'baudrate': baudrate,
                    'response': result.get('response', '')
                }, f"Найдено: адрес {address}, скорость {baudrate} baud"
    
    return None, "Устройство не найдено"
