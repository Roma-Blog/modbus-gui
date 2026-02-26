#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modbus Scanner Rust Wrapper
Обёртка для Rust библиотеки быстрого сканирования Modbus устройств
"""

import os
import sys
from typing import Optional, List, Callable, Dict, Any

# Путь к Rust библиотеке
RUST_LIB_PATH = os.path.join(os.path.dirname(__file__), 'modbus_scanner_rust')

# Стандартные скорости для перебора
DEFAULT_BAUDRATES = [115200, 57600, 38400, 19200, 9600]


class ModbusScannerRust:
    """
    Python обёртка для Rust Modbus сканера
    
    Обеспечивает быстрый перебор адресов и скоростей Modbus RTU устройств
    с использованием нативного кода (Rust + PyO3)
    """
    
    def __init__(self, port: str, timeout_ms: int = 100):
        """
        Инициализация сканера
        
        Args:
            port: COM порт (например, '/dev/ttyUSB0', 'COM1')
            timeout_ms: Таймаут операции в миллисекундах
        """
        self.port = port
        self.timeout_ms = timeout_ms
        self._scanner = None
        self._load_library()
    
    def _load_library(self):
        """Загружает Rust библиотеку"""
        try:
            # Пробуем загрузить скомпилированную библиотеку
            import modbus_scanner_rust
            self._scanner = modbus_scanner_rust.ModbusScanner(self.port, self.timeout_ms)
        except ImportError:
            # Библиотека не скомпилирована - используем заглушку
            print(f"[WARNING] Rust библиотека не найдена. Запуск в режиме эмуляции.")
            print(f"[INFO] Для компиляции выполните: cd {RUST_LIB_PATH} && maturin develop")
            self._scanner = None
    
    def scan_single(self, address: int, baudrate: int, 
                    status_callback: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        """
        Сканирует один адрес на одной скорости
        
        Args:
            address: Адрес устройства (1-247)
            baudrate: Скорость соединения
            status_callback: Функция для обновления статуса (опционально)
            
        Returns:
            Словарь с результатом или None если устройство не найдено
        """
        if self._scanner is None:
            return self._scan_single_fallback(address, baudrate, status_callback)
        
        try:
            result = self._scanner.scan_single(address, baudrate)
            if result:
                return {
                    'address': result.address,
                    'baudrate': result.baudrate,
                    'response': result.response,
                }
            return None
        except Exception as e:
            if status_callback:
                status_callback(f"Ошибка сканирования: {e}")
            return None
    
    def _scan_single_fallback(self, address: int, baudrate: int,
                               status_callback: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        """Резервная реализация на Python (если Rust библиотека не доступна)"""
        # Это заглушка - в реальном проекте можно использовать существующий ModbusRTUClient
        if status_callback:
            status_callback(f"[FALLBACK] Проверка адреса {address} @ {baudrate}")
        return None
    
    def scan_addresses(self, baudrate: int, start_address: int = 1, end_address: int = 200,
                       status_callback: Optional[Callable[[str], None]] = None) -> List[Dict[str, Any]]:
        """
        Сканирует диапазон адресов на одной скорости
        
        Args:
            baudrate: Скорость соединения
            start_address: Начальный адрес (включительно)
            end_address: Конечный адрес (включительно)
            status_callback: Функция для обновления статуса (опционально)
            
        Returns:
            Список найденных устройств
        """
        if self._scanner is None:
            return []
        
        def callback(status: str):
            if status_callback:
                status_callback(status)
        
        try:
            results = self._scanner.scan_addresses(
                baudrate, start_address, end_address, callback
            )
            return [
                {
                    'address': r.address,
                    'baudrate': r.baudrate,
                    'response': r.response,
                }
                for r in results
            ]
        except Exception as e:
            if status_callback:
                status_callback(f"Ошибка сканирования: {e}")
            return []
    
    def scan_all(self, baudrates: Optional[List[int]] = None,
                 start_address: int = 1, end_address: int = 200,
                 status_callback: Optional[Callable[[str], None]] = None) -> List[Dict[str, Any]]:
        """
        Сканирует все комбинации адресов и скоростей
        
        Args:
            baudrates: Список скоростей для проверки (по умолчанию [115200, 57600, 38400, 19200, 9600])
            start_address: Начальный адрес (включительно)
            end_address: Конечный адрес (включительно)
            status_callback: Функция для обновления статуса (опционально)
            
        Returns:
            Список найденных устройств
        """
        if baudrates is None:
            baudrates = DEFAULT_BAUDRATES
        
        if self._scanner is None:
            return []
        
        def callback(status: str):
            if status_callback:
                status_callback(status)
        
        try:
            results = self._scanner.scan_all(
                baudrates, start_address, end_address, callback
            )
            return [
                {
                    'address': r.address,
                    'baudrate': r.baudrate,
                    'response': r.response,
                }
                for r in results
            ]
        except Exception as e:
            if status_callback:
                status_callback(f"Ошибка сканирования: {e}")
            return []
    
    def scan_first_found(self, baudrate: int, start_address: int = 1, end_address: int = 200,
                         status_callback: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        """
        Сканирует и возвращает первое найденное устройство
        
        Args:
            baudrate: Скорость соединения
            start_address: Начальный адрес (включительно)
            end_address: Конечный адрес (включительно)
            status_callback: Функция для обновления статуса (опционально)
            
        Returns:
            Информация о первом найденном устройстве или None
        """
        if self._scanner is None:
            return None
        
        def callback(status: str):
            if status_callback:
                status_callback(status)
        
        try:
            result = self._scanner.scan_first_found(baudrate, start_address, end_address, callback)
            if result:
                return {
                    'address': result.address,
                    'baudrate': result.baudrate,
                    'response': result.response,
                }
            return None
        except Exception as e:
            if status_callback:
                status_callback(f"Ошибка сканирования: {e}")
            return None
    
    def auto_detect_address(self, baudrate: int, start_address: int = 1, end_address: int = 200,
                            status_callback: Optional[Callable[[str], None]] = None) -> Optional[int]:
        """
        Быстрое определение адреса устройства на известной скорости
        
        Args:
            baudrate: Скорость соединения
            start_address: Начальный адрес (включительно)
            end_address: Конечный адрес (включительно)
            status_callback: Функция для обновления статуса (опционально)
            
        Returns:
            Адрес устройства или None
        """
        result = self.scan_first_found(baudrate, start_address, end_address, status_callback)
        return result['address'] if result else None
    
    def auto_detect_baudrate(self, address: int,
                             baudrates: Optional[List[int]] = None,
                             status_callback: Optional[Callable[[str], None]] = None) -> Optional[int]:
        """
        Быстрое определение скорости устройства на известном адресе
        
        Args:
            address: Адрес устройства
            baudrates: Список скоростей для проверки
            status_callback: Функция для обновления статуса (опционально)
            
        Returns:
            Скорость соединения или None
        """
        if baudrates is None:
            baudrates = DEFAULT_BAUDRATES
        
        for baudrate in baudrates:
            if status_callback:
                status_callback(f"Проверка скорости {baudrate}...")
            
            result = self.scan_single(address, baudrate, status_callback)
            if result:
                return baudrate
        
        return None


def quick_scan(port: str,
               baudrates: Optional[List[int]] = None,
               start_address: int = 1,
               end_address: int = 200,
               timeout_ms: int = 100,
               status_callback: Optional[Callable[[str], None]] = None) -> List[Dict[str, Any]]:
    """
    Быстрое сканирование Modbus устройств (удобная функция)
    
    Args:
        port: COM порт
        baudrates: Список скоростей для проверки
        start_address: Начальный адрес
        end_address: Конечный адрес
        timeout_ms: Таймаут операции
        status_callback: Функция для обновления статуса
        
    Returns:
        Список найденных устройств
    """
    scanner = ModbusScannerRust(port, timeout_ms)
    return scanner.scan_all(baudrates, start_address, end_address, status_callback)
