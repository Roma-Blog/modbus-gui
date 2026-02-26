#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Constants Module
Константы и маппинги для Modbus GUI приложения

Кроссплатформенная версия (Linux + Windows)
"""

import sys

# Определение платформы
IS_WINDOWS = sys.platform.startswith('win')
IS_LINUX = sys.platform.startswith('linux')
IS_MACOS = sys.platform.startswith('darwin')

# Скорости Modbus RTU
MODBUS_SPEED_MAP = {
    0: "2400",
    1: "4800",
    2: "9600",
    3: "19200",
    4: "38400",
    5: "57600",
    6: "115200"
}

MODBUS_SPEED_REVERSE_MAP = {
    "2400": 0,
    "4800": 1,
    "9600": 2,
    "19200": 3,
    "38400": 4,
    "57600": 5,
    "115200": 6
}

# Скорости CAN
CAN_SPEED_MAP = {
    0: "10K",
    1: "20K",
    2: "50K",
    3: "125K",
    4: "250K",
    5: "500K",
    6: "800K",
    7: "1000K"
}

CAN_SPEED_REVERSE_MAP = {
    "10K": 0,
    "20K": 1,
    "50K": 2,
    "125K": 3,
    "250K": 4,
    "500K": 5,
    "800K": 6,
    "1000K": 7
}

# Адреса регистров
REGISTER_ADDRESSES = {
    "CHANNELS": 1,  # Регистры 1-2: каналы
    "MODBUS_SPEED": 3,  # Регистр 3: скорость Modbus
    "MODBUS_ADDRESS": 6,  # Регистр 6: адрес Modbus
    "CAN_PARAMS": 10  # Регистры 10-11: CAN параметры
}

# Адреса coils
COIL_ADDRESSES = {
    "CHANNEL1_START": 0,  # Канал 1: coils 0-...
    "CHANNEL2_START": 32  # Канал 2: coils 32-...
}

# Режимы тестирования
TEST_MODES = {
    "RUNNING_LIGHTS": "running_lights",
    "FULL_SWITCH": "full_switch",
    "SNAKE": "snake"
}

# Стандартные COM порты (кроссплатформенно)
if IS_WINDOWS:
    DEFAULT_COM_PORTS = ["COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8"]
elif IS_MACOS:
    DEFAULT_COM_PORTS = ["/dev/cu.usbserial-1", "/dev/cu.usbmodem1", "/dev/cu.SLAB_USBtoUART"]
else:  # Linux
    DEFAULT_COM_PORTS = ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyUSB2", "/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyS0"]

# Стандартные скорости
DEFAULT_BAUDRATES = ["Автоопределение", "9600", "19200", "38400", "57600", "115200"]

# Конфигурация автопоиска
AUTO_SEARCH_CONFIG = {
    "MIN_ADDRESS": 1,
    "MAX_ADDRESS": 200,
    "BAUDRATES": [115200, 57600, 38400, 19200, 9600],  # Порядок перебора: от высокой к низкой
    "TIMEOUT_MS": 100,
    "ENABLED_BY_DEFAULT": True
}

# Стандартные CAN скорости
DEFAULT_CAN_SPEEDS = ["100K", "125K", "250K", "500K", "1000K"]

# Стандартные CAN адреса
DEFAULT_CAN_ADDRESSES = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]

# Таймеры
TIMER_INTERVALS = {
    "UPDATE_UI": 2000,  # 2 секунды
    "AUTO_TEST": 500,   # 0.5 секунды
    "RUNNING_LIGHTS": 500,  # 0.5 секунды
    "SNAKE": 500,       # 0.5 секунды
    "CONNECTION_TIMEOUT": 2000  # 2 секунды
}

# Лимиты
LIMITS = {
    "MIN_DEVICE_ADDRESS": 1,
    "MAX_DEVICE_ADDRESS": 247,
    "MIN_CAN_ADDRESS": 1,
    "MAX_CAN_ADDRESS": 127,
    "MAX_COILS_PER_CHANNEL": 65535
}

# Сообщения
MESSAGES = {
    "CONNECTION_SUCCESS": "Соединение установлено",
    "CONNECTION_FAILED": "Ошибка подключения",
    "CONFIG_READ_SUCCESS": "Конфигурация прочитана",
    "CONFIG_WRITE_SUCCESS": "Конфигурация записана",
    "TEST_STARTED": "Тест запущен",
    "TEST_STOPPED": "Тест остановлен",
    "DEVICE_NOT_FOUND": "Устройство не найдено",
    "PORT_NOT_AVAILABLE": "Порт недоступен"
}

# Стили кнопок
BUTTON_STYLES = {
    "CONNECT": """
        QPushButton {
            background-color: #28a745;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #218838;
        }
        QPushButton:pressed {
            background-color: #1e7e34;
        }
    """,
    "DISCONNECT": """
        QPushButton {
            background-color: #dc3545;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #c82333;
        }
        QPushButton:pressed {
            background-color: #bd2130;
        }
    """
}