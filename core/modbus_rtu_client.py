#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modbus RTU Client Module
Основной клиент для работы с Modbus RTU устройствами
"""

from .modbus_connection import ModbusConnection
from .modbus_device_info import ModbusDeviceInfo
from .modbus_registers import ModbusRegisters
import logging
from typing import Optional, List

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    force=True)
logger = logging.getLogger(__name__)

class ModbusRTUClient:
    """Клиент для работы с Modbus RTU устройствами"""

    def __init__(self, port: str, device_address: int, baudrate: Optional[int] = None, status_callback=None):
        """
        Инициализация Modbus RTU клиента

        Args:
            port: COM порт (например, 'COM1', '/dev/ttyUSB0')
            device_address: Адрес Modbus устройства (1-247)
            baudrate: Скорость соединения (если None, будет автоматически определена)
            status_callback: Функция для обновления статуса (для GUI)
        """
        self.port = port
        self.device_address = device_address
        self.baudrate = baudrate
        self.status_callback = status_callback
        self.connection = ModbusConnection(port, baudrate, status_callback)
        self.device_info = None
        self.registers = None

    def connect(self):
        """
        Устанавливает соединение с устройством

        Returns:
            tuple: (bool, str) - успех и сообщение
        """
        return self.connection.connect()

    def get_device_info(self) -> Optional[dict]:
        """
        Получает информацию об устройстве

        Returns:
            dict или None: Информация об устройстве
        """
        if not self.connection.connection:
            logger.error("Соединение не установлено")
            return None

        self.device_info = ModbusDeviceInfo(self.connection.connection, self.device_address)
        return self.device_info.get_device_info()

    def read_holding_registers(self, start_address: int, count: int) -> Optional[list]:
        """
        Читает holding регистры

        Args:
            start_address: Начальный адрес регистра
            count: Количество регистров для чтения

        Returns:
            list или None: Список значений регистров
        """
        if not self.connection.connection:
            logger.error("Соединение не установлено")
            return None

        self.registers = ModbusRegisters(self.connection.connection, self.device_address)
        return self.registers.read_holding_registers(start_address, count)

    def write_holding_registers(self, start_address: int, values: List[int]) -> bool:
        """
        Записывает holding регистры

        Args:
            start_address: Начальный адрес регистра
            values: Список значений для записи

        Returns:
            bool: True если запись успешна, False иначе
        """
        if not self.connection.connection:
            logger.error("Соединение не установлено")
            return False

        self.registers = ModbusRegisters(self.connection.connection, self.device_address)
        return self.registers.write_holding_registers(start_address, values)

    def write_single_register(self, address: int, value: int) -> bool:
        """
        Записывает один holding регистр

        Args:
            address: Адрес регистра
            value: Значение для записи

        Returns:
            bool: True если запись успешна, False иначе
        """
        if not self.connection.connection:
            logger.error("Соединение не установлено")
            return False

        self.registers = ModbusRegisters(self.connection.connection, self.device_address)
        return self.registers.write_single_register(address, value)

    def write_single_coil(self, address: int, value: bool) -> bool:
        """
        Записывает один coil

        Args:
            address: Адрес coil
            value: Значение для записи (True/False)

        Returns:
            bool: True если запись успешна, False иначе
        """
        if not self.connection.connection:
            logger.error("Соединение не установлено")
            return False

        self.registers = ModbusRegisters(self.connection.connection, self.device_address)
        return self.registers.write_single_coil(address, value)

    def write_multiple_coils(self, start_address: int, values: List[bool]) -> bool:
        """
        Записывает несколько coils

        Args:
            start_address: Начальный адрес coil
            values: Список значений для записи (True/False)

        Returns:
            bool: True если запись успешна, False иначе
        """
        if not self.connection.connection:
            logger.error("Соединение не установлено")
            return False

        self.registers = ModbusRegisters(self.connection.connection, self.device_address)
        return self.registers.write_multiple_coils(start_address, values)

    def disconnect(self):
        """Закрывает соединение"""
        self.connection.disconnect()

    def __enter__(self):
        """Поддержка контекстного менеджера"""
        success, message = self.connect()
        if not success:
            raise RuntimeError(f"Не удалось подключиться: {message}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Поддержка контекстного менеджера"""
        self.disconnect()
