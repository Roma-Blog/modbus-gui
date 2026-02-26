#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modbus Worker Thread Module
Модуль для потока работы с Modbus устройствами

С интеграцией Rust сканера для быстрого автоопределения адресов и скоростей
"""

import sys
import os

from PyQt5.QtCore import QThread, pyqtSignal
from typing import Optional, List
from datetime import datetime

# Глобальная переменная для хранения ошибки импорта
_import_error = None

# Попытка импорта Rust сканера для быстрого перебора
_rust_scanner_available = False
try:
    from modbus_scanner_wrapper import ModbusScannerRust
    _rust_scanner_available = True
    print("[INFO] Rust сканер загружен - быстрый перебор адресов/скоростей доступен")
except ImportError as e:
    print(f"[WARNING] Rust сканер недоступен: {e}")
    print("[INFO] Для ускорения перебора установите: pip install maturin && cd modbus_scanner_rust && maturin develop --release")
    ModbusScannerRust = None

try:
    from core.modbus_rtu_client import ModbusRTUClient
    from core.device_response_parser_fixed import parse_specific_device_response
except ImportError as e:
    import traceback
    _import_error = str(e)
    error_msg = f"Ошибка импорта модулей: {e}\n{traceback.format_exc()}"
    print(error_msg)
    # Создаем заглушки если модули недоступны
    class ModbusRTUClient:
        def __init__(self, *args, **kwargs): pass
        def connect(self): return False, f"Модуль недоступен: {_import_error}"
        def get_device_info(self): return None
        def read_holding_registers(self, *args, **kwargs): return None
        def write_holding_registers(self, *args, **kwargs): return False
        def write_multiple_coils(self, *args, **kwargs): return False
        def disconnect(self): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass

    def parse_specific_device_response(hex_response):
        return {"error": f"Модуль парсера недоступен: {_import_error}"}

    # Отправляем ошибку в GUI
    try:
        # Если мы в контексте потока, можем отправить сигнал
        # Но поскольку это на уровне модуля, добавим глобальную переменную
        import __main__
        if hasattr(__main__, 'worker_thread') and __main__.worker_thread:
            __main__.worker_thread.error_occurred.emit(f"Критическая ошибка импорта: {_import_error}")
    except:
        pass

class ModbusWorkerThread(QThread):
    """Поток для выполнения операций Modbus"""

    # Сигналы для обновления GUI
    connected = pyqtSignal(bool, str)
    data_received = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    status_updated = pyqtSignal(str)

    def __init__(self, port: str, address: int, baudrate: Optional[int] = None):
        super().__init__()
        self.port = port
        self.address = address
        self.baudrate = baudrate
        self.client = None
        self.is_connected = False
        self.should_stop = False

    def run(self):
        """Основной цикл потока - простое открытие порта"""
        try:
            self.status_updated.emit("Открытие COM порта...")

            # Создаем клиент
            self.client = ModbusRTUClient(self.port, self.address, self.baudrate, status_callback=self.status_updated.emit)

            # Просто открываем порт
            success, message = self.client.connect()
            if success:
                self.is_connected = True
                baudrate_info = getattr(self.client, 'baudrate', 'неизвестная')
                self.connected.emit(True, f"Порт {self.port} открыт @ {baudrate_info} baud")
                self.status_updated.emit("✓ Подключено")

                # Ждем команд от GUI
                while not self.should_stop and self.is_connected:
                    self.msleep(100)  # Короткая пауза для предотвращения загрузки CPU
            else:
                self.connected.emit(False, message)

        except Exception as e:
            self.connected.emit(False, f"Ошибка открытия порта: {str(e)}")
        finally:
            if self.client:
                self.client.disconnect()

    def stop(self):
        """Остановить поток"""
        self.should_stop = True
        self.is_connected = False
        if self.client:
            self.client.disconnect()

    def read_device_info(self):
        """Прочитать информацию об устройстве (без логирования)"""
        if self.client and self.is_connected:
            try:
                raw_device_info = self.client.get_device_info()
                if raw_device_info:
                    # Применяем парсер для получения структурированных данных
                    hex_response = raw_device_info.get('raw_response') or raw_device_info.get('hex_format')
                    if hex_response:
                        parsed_info = parse_specific_device_response(hex_response)
                        # Объединяем сырые данные с распарсенными
                        combined_info = {**raw_device_info, **parsed_info}
                        self.data_received.emit(combined_info)
                        return combined_info
                    else:
                        self.data_received.emit(raw_device_info)
                        return raw_device_info
                else:
                    self.error_occurred.emit("Устройство не отвечает")
                    return None
            except Exception as e:
                self.error_occurred.emit(f"Ошибка чтения: {str(e)}")
                return None
        else:
            self.error_occurred.emit("Соединение не установлено")
            return None

    def auto_detect_baudrate_with_command17(self):
        """
        Автоопределение скорости через команду 17 (Read Device Identification)
        Использует Rust сканер для быстрого перебора скоростей

        Returns:
            tuple: (device_info, baudrate) или (None, None) при неудаче
        """
        # Стандартные скорости для перебора (начиная с высоких)
        standard_baudrates = [115200, 57600, 38400, 19200, 9600]

        self.status_updated.emit("Автоопределение скорости через команду 17...")

        # Проверяем доступность Rust сканера
        if _rust_scanner_available and ModbusScannerRust:
            return self._auto_detect_baudrate_rust(standard_baudrates)
        
        # Используем старый Python метод если Rust недоступен
        return self._auto_detect_baudrate_python(standard_baudrates)
    
    def _auto_detect_baudrate_rust(self, standard_baudrates: List[int]):
        """Быстрое определение скорости с использованием Rust сканера"""
        self.status_updated.emit("Используется Rust сканер для ускоренного перебора...")
        
        scanner = ModbusScannerRust(self.port, timeout_ms=100)
        
        for baudrate in standard_baudrates:
            self.status_updated.emit(f"Проверка скорости {baudrate} baud...")
            
            # Быстрая проверка первых 10 адресов на этой скорости
            result = scanner.scan_first_found(
                baudrate=baudrate,
                start_address=1,
                end_address=10,
                status_callback=lambda s: None  # Не спамим статусами для каждой проверки
            )
            
            if result:
                self.status_updated.emit(f"Найдена рабочая скорость: {baudrate} baud (адрес {result['address']})")
                
                # Подключаемся на найденной скорости для дальнейшей работы
                if self.client:
                    self.client.disconnect()
                
                self.baudrate = baudrate
                self.address = result['address']
                self.client = ModbusRTUClient(self.port, self.address, baudrate, status_callback=self.status_updated.emit)
                success, _ = self.client.connect()
                
                if success:
                    self.is_connected = True
                    device_info = self.client.get_device_info()
                    if device_info:
                        hex_response = device_info.get('raw_response') or device_info.get('hex_format')
                        if hex_response:
                            parsed_info = parse_specific_device_response(hex_response)
                            combined_info = {**device_info, **parsed_info}
                        else:
                            combined_info = device_info
                        return combined_info, baudrate
                
                return device_info, baudrate
        
        self.status_updated.emit("Не удалось определить скорость - устройство не отвечает")
        return None, None
    
    def _auto_detect_baudrate_python(self, standard_baudrates: List[int]):
        """Определение скорости через Python (резервный метод)"""
        # Сохраняем текущий клиент для восстановления в случае неудачи
        original_client = self.client
        original_is_connected = self.is_connected

        # Временно отключаемся от текущего клиента
        if self.client:
            self.client.disconnect()
            self.is_connected = False

        try:
            for baudrate in standard_baudrates:
                self.status_updated.emit(f"Проверка скорости {baudrate} baud...")

                try:
                    # Создаем новый клиент с проверяемой скоростью
                    temp_client = ModbusRTUClient(self.port, self.address, baudrate)

                    # Проверяем подключение
                    success, _ = temp_client.connect()
                    if success:
                        # Отправляем команду 17
                        device_info = temp_client.get_device_info()

                        if device_info:
                            # Применяем парсер к найденным данным
                            hex_response = device_info.get('raw_response') or device_info.get('hex_format')
                            if hex_response:
                                parsed_info = parse_specific_device_response(hex_response)
                                # Объединяем сырые данные с распарсенными
                                combined_info = {**device_info, **parsed_info}
                            else:
                                combined_info = device_info

                            # Успешно! Устанавливаем новый клиент
                            self.client = temp_client
                            self.baudrate = baudrate
                            self.is_connected = True
                            self.status_updated.emit(f"Найдена рабочая скорость: {baudrate} baud")
                            return combined_info, baudrate
                        else:
                            temp_client.disconnect()
                    else:
                        temp_client.disconnect()

                except Exception as e:
                    self.status_updated.emit(f"Ошибка на скорости {baudrate}: {str(e)}")
                    continue

            # Если ничего не нашли, восстанавливаем оригинальный клиент
            self.client = original_client
            self.is_connected = original_is_connected
            self.status_updated.emit("Не удалось определить скорость - устройство не отвечает")
            return None, None

        except Exception as e:
            # В случае критической ошибки восстанавливаем оригинальный клиент
            self.client = original_client
            self.is_connected = original_is_connected
            self.status_updated.emit(f"Критическая ошибка автоопределения: {str(e)}")
            return None, None

    def auto_detect_address_with_command17(self, port: str, baudrate: int):
        """
        Автоопределение адреса устройства через команду 17 (Read Device Identification)
        Использует Rust сканер для быстрого перебора адресов

        Args:
            port: COM порт
            baudrate: Скорость соединения

        Returns:
            tuple: (device_info, address) или (None, None) при неудаче
        """
        self.status_updated.emit("Автоопределение адреса через команду 17...")

        # Проверяем доступность Rust сканера
        if _rust_scanner_available and ModbusScannerRust:
            return self._auto_detect_address_rust(port, baudrate)
        
        # Используем старый Python метод если Rust недоступен
        return self._auto_detect_address_python(port, baudrate)
    
    def _auto_detect_address_rust(self, port: str, baudrate: int):
        """Быстрое определение адреса с использованием Rust сканера"""
        self.status_updated.emit("Используется Rust сканер для ускоренного перебора адресов...")
        
        scanner = ModbusScannerRust(port, timeout_ms=100)
        
        # Сначала проверяем адрес по умолчанию (4)
        self.status_updated.emit(f"Проверка адреса 4 (по умолчанию)...")
        result = scanner.scan_single(address=4, baudrate=baudrate)
        
        if result:
            self.status_updated.emit(f"Устройство найдено на адресе 4")
            return self._create_device_info(port, 4, baudrate, result['response'])
        
        # Быстрый перебор адресов 1-200
        self.status_updated.emit("Перебор адресов 1-200...")
        
        def status_callback(status):
            # Показываем статус только для каждых 10 адресов чтобы не спамить
            if "Адрес" in status:
                import re
                match = re.search(r'Адрес (\d+)', status)
                if match:
                    addr = int(match.group(1))
                    if addr % 10 == 0 or addr == 1:
                        self.status_updated.emit(f"Проверка адреса {addr}/200...")
        
        results = scanner.scan_addresses(
            baudrate=baudrate,
            start_address=1,
            end_address=200,
            status_callback=status_callback
        )
        
        if results:
            found = results[0]
            self.status_updated.emit(f"Устройство найдено на адресе {found['address']}")
            return self._create_device_info(port, found['address'], baudrate, found['response'])
        
        self.status_updated.emit("Устройство не найдено ни на одном адресе")
        return None, None
    
    def _create_device_info(self, port: str, address: int, baudrate: int, response: str):
        """Создаёт структуру device_info из результата Rust сканера"""
        # Подключаемся на найденных параметрах для получения полной информации
        if self.client:
            self.client.disconnect()
        
        self.address = address
        self.baudrate = baudrate
        self.client = ModbusRTUClient(port, address, baudrate, status_callback=self.status_updated.emit)
        success, _ = self.client.connect()
        
        if success:
            self.is_connected = True
            device_info = self.client.get_device_info()
            if device_info:
                hex_response = device_info.get('raw_response') or device_info.get('hex_format')
                if hex_response:
                    parsed_info = parse_specific_device_response(hex_response)
                    combined_info = {**device_info, **parsed_info}
                else:
                    combined_info = device_info
                return combined_info, address
        
        # Возвращаем базовую информацию даже если не удалось подключиться
        return {
            'device_address': address,
            'raw_response': response.replace(' ', ''),
            'hex_format': response,
        }, address
    
    def _auto_detect_address_python(self, port: str, baudrate: int):
        """Определение адреса через Python (резервный метод)"""
        # Сначала пробуем адрес по умолчанию (4)
        default_address = 4
        self.status_updated.emit(f"Проверка адреса {default_address}...")

        try:
            # Создаем временный клиент для проверки адреса
            temp_client = ModbusRTUClient(port, default_address, baudrate)

            # Пробуем подключиться
            success, _ = temp_client.connect()
            if success:
                # Отправляем команду 17
                device_info = temp_client.get_device_info()

                if device_info:
                    # Применяем парсер к найденным данным
                    hex_response = device_info.get('raw_response') or device_info.get('hex_format')
                    if hex_response:
                        parsed_info = parse_specific_device_response(hex_response)
                        # Объединяем сырые данные с распарсенными
                        combined_info = {**device_info, **parsed_info}
                    else:
                        combined_info = device_info

                    temp_client.disconnect()
                    self.status_updated.emit(f"Устройство найдено на адресе {default_address}")
                    return combined_info, default_address
                else:
                    temp_client.disconnect()
        except Exception as e:
            self.status_updated.emit(f"Ошибка при проверке адреса {default_address}: {str(e)}")

        # Если адрес 4 не сработал, перебираем первые 20 адресов
        for address in range(1, 21):
            if address == 4:  # Уже проверяли
                continue

            self.status_updated.emit(f"Проверка адреса {address}...")

            try:
                # Создаем временный клиент для проверки адреса
                temp_client = ModbusRTUClient(port, address, baudrate)

                # Пробуем подключиться
                success, _ = temp_client.connect()
                if success:
                    # Отправляем команду 17
                    device_info = temp_client.get_device_info()

                    if device_info:
                        # Применяем парсер к найденным данным
                        hex_response = device_info.get('raw_response') or device_info.get('hex_format')
                        if hex_response:
                            parsed_info = parse_specific_device_response(hex_response)
                            # Объединяем сырые данные с распарсенными
                            combined_info = {**device_info, **parsed_info}
                        else:
                            combined_info = device_info

                        temp_client.disconnect()
                        self.status_updated.emit(f"Устройство найдено на адресе {address}")
                        return combined_info, address
                    else:
                        temp_client.disconnect()
            except Exception as e:
                self.status_updated.emit(f"Ошибка при проверке адреса {address}: {str(e)}")
                continue

        self.status_updated.emit("Устройство не найдено ни на одном адресе")
        return None, None

    def read_device_id(self):
        """Прочитать ID устройства (синоним для read_device_info)"""
        return self.read_device_info()

    def read_holding_registers(self, start_address: int = 0, count: int = 13):
        """Прочитать holding регистры"""
        if self.client and self.is_connected:
            try:
                registers = self.client.read_holding_registers(start_address, count)
                if registers is not None:
                    # Создаем словарь с данными регистров
                    register_data = {
                        "holding_registers": registers,
                        "start_address": start_address,
                        "count": count,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    self.data_received.emit(register_data)
                    return register_data
                else:
                    self.error_occurred.emit("Не удалось прочитать holding регистры")
                    return None
            except Exception as e:
                self.error_occurred.emit(f"Ошибка чтения регистров: {str(e)}")
                return None
        else:
            self.error_occurred.emit("Соединение не установлено")
            return None

    def read_error_info(self):
        """Прочитать информацию об ошибках (заглушка)"""
        # Здесь должна быть логика чтения регистров ошибок
        # Пока возвращаем заглушку
        return {
            "error_code": 0,
            "error_description": "Ошибок не обнаружено",
            "last_error_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def write_holding_registers(self, start_address: int, values: List[int]):
        """Записать holding регистры"""
        if self.client and self.is_connected:
            try:
                success = self.client.write_holding_registers(start_address, values)
                if success:
                    result_data = {
                        "status": "success",
                        "message": f"Записано {len(values)} регистров начиная с адреса {start_address}",
                        "start_address": start_address,
                        "values": values,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    self.data_received.emit(result_data)
                    return result_data
                else:
                    self.error_occurred.emit("Не удалось записать holding регистры")
                    return {
                        "status": "error",
                        "message": "Не удалось записать holding регистры",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
            except Exception as e:
                self.error_occurred.emit(f"Ошибка записи регистров: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Ошибка записи регистров: {str(e)}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        else:
            self.error_occurred.emit("Соединение не установлено")
            return {
                "status": "error",
                "message": "Соединение не установлено",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    def write_coils(self, start_address: int, values: List[bool]):
        """Записать coils"""
        if self.client and self.is_connected:
            try:
                success = self.client.write_multiple_coils(start_address, values)
                if success:
                    result_data = {
                        "status": "success",
                        "message": f"Записано {len(values)} coils начиная с адреса {start_address}",
                        "start_address": start_address,
                        "values": values,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    self.data_received.emit(result_data)
                    return result_data
                else:
                    self.error_occurred.emit("Не удалось записать coils")
                    return {
                        "status": "error",
                        "message": "Не удалось записать coils",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
            except Exception as e:
                self.error_occurred.emit(f"Ошибка записи coils: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Ошибка записи coils: {str(e)}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        else:
            self.error_occurred.emit("Соединение не установлено")
            return {
                "status": "error",
                "message": "Соединение не установлено",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
