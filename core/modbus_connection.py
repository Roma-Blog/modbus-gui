#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modbus Connection Module
Модуль для управления соединением и автоматического определения скорости
"""

import serial
import time
import logging
from typing import Optional, List, Union
import sys
import os
import json

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    force=True)
logger = logging.getLogger(__name__)

def load_config():
    """Загружает конфигурацию из JSON файла"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logger.warning(f"Файл конфигурации {config_path} не найден, используются значения по умолчанию")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка чтения конфигурации: {e}")
        return {}

class ModbusConnection:
    """Класс для управления соединением с Modbus RTU устройствами"""

    # Стандартные скорости для перебора (начинаем с высоких для быстроты)
    STANDARD_BAUDRATES = []

    def __init__(self, port: str, baudrate: Optional[int] = None, status_callback=None):
        """
        Инициализация соединения

        Args:
            port: COM порт (например, 'COM1', '/dev/ttyUSB0')
            baudrate: Скорость соединения (если None, будет автоматически определена)
            status_callback: Функция для обновления статуса (для GUI)
        """
        self.port = port
        self.baudrate: Optional[int] = baudrate
        self.connection = None
        self.status_callback = status_callback

    def connect(self):
        """
        Устанавливает соединение с устройством

        Returns:
            tuple: (bool, str) - успех и сообщение
        """
        try:
            if self.baudrate is None:
                success, message = self._auto_detect_baudrate()
                return success, message
            else:
                success, message = self._connect_with_known_baudrate()
                return success, message
        except KeyboardInterrupt:
            logger.info("Подключение прервано пользователем")
            return False, "Подключение прервано пользователем"
        except Exception as e:
            logger.error(f"Ошибка при подключении: {e}")
            if self.connection and hasattr(self.connection, 'is_open') and self.connection.is_open:
                try:
                    self.connection.close()
                except:
                    pass
            return False, f"Ошибка при подключении: {str(e)}"

    def _connect_with_known_baudrate(self):
        """Подключение с известной скоростью"""
        try:
            if not self.port or not self.baudrate:
                logger.error("Не указаны порт или скорость для подключения")
                return False, "Не указаны порт или скорость для подключения"

            if self.connection and hasattr(self.connection, 'is_open') and self.connection.is_open:
                try:
                    self.connection.close()
                except:
                    pass

            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0
            )

            if hasattr(self.connection, 'is_open') and self.connection.is_open:
                logger.info(f"Подключение установлено: {self.port} @ {self.baudrate} baud")
                return True, f"Подключение установлено: {self.port} @ {self.baudrate} baud"
            else:
                logger.error(f"Не удалось открыть порт {self.port}")
                try:
                    self.connection.close()
                except:
                    pass
                self.connection = None
                return False, f"Не удалось открыть порт {self.port}"

        except KeyboardInterrupt:
            logger.info("Подключение прервано пользователем")
            return False, "Подключение прервано пользователем"
        except Exception as e:
            logger.error(f"Ошибка подключения к {self.port}: {e}")
            try:
                if self.connection:
                    self.connection.close()
            except:
                pass
            self.connection = None
            return False, f"Ошибка подключения к {self.port}: {str(e)}"

    def _auto_detect_baudrate(self):
        """
        Автоматическое определение скорости соединения
        Перебирает стандартные скорости и отправляет команду 17
        """
        print(f"Автоопределение скорости для порта {self.port}...")
        logger.info(f"Автоматическое определение скорости для порта {self.port}")

        if self.status_callback:
            self.status_callback(f"Автоопределение скорости для порта {self.port}...")

        for baudrate in self.STANDARD_BAUDRATES:
            print(f"Проверка скорости {baudrate} baud...")
            logger.info(f"Попытка подключения на скорости {baudrate} baud...")

            if self.status_callback:
                self.status_callback(f"Проверка скорости {baudrate} baud...")

            try:
                connection = serial.Serial(
                    port=self.port,
                    baudrate=baudrate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=0.5
                )

                if not connection.is_open:
                    print(f"Не удалось открыть порт {self.port} на скорости {baudrate}")
                    connection.close()
                    continue

                self.connection = connection
                self.baudrate = baudrate
                print(f"[SUCCESS] Успешное подключение на скорости {baudrate} baud")
                logger.info(f"[SUCCESS] Успешное подключение на скорости {baudrate} baud")
                if self.status_callback:
                    self.status_callback(f"Успешное подключение на скорости {baudrate} baud")
                return True, f"Успешное подключение на скорости {baudrate} baud"

            except Exception as e:
                print(f"Ошибка на скорости {baudrate}: {str(e)}")
                logger.debug(f"Ошибка на скорости {baudrate}: {e}")
                if self.status_callback:
                    self.status_callback(f"Ошибка на скорости {baudrate} baud")
                time.sleep(0.1)
                continue

        print(f"Не удалось найти рабочую скорость для порта {self.port}")
        logger.error(f"Не удалось найти рабочую скорость для порта {self.port}")
        if self.status_callback:
            self.status_callback(f"Не удалось определить скорость для порта {self.port}")
        return False, f"Не удалось найти рабочую скорость для порта {self.port}"

    def disconnect(self):
        """Закрывает соединение"""
        try:
            if self.connection:
                if hasattr(self.connection, 'is_open') and self.connection.is_open:
                    self.connection.close()
                    logger.info("Соединение закрыто")
                elif hasattr(self.connection, 'close'):
                    self.connection.close()
                    logger.info("Соединение закрыто (принудительно)")
        except Exception as e:
            logger.warning(f"Ошибка при закрытии соединения: {e}")
        finally:
            self.connection = None

    def __enter__(self):
        """Поддержка контекстного менеджера"""
        success, message = self.connect()
        if not success:
            raise RuntimeError(f"Не удалось подключиться: {message}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Поддержка контекстного менеджера"""
        self.disconnect()

# Загружаем конфигурацию один раз при импорте модуля
_config = load_config()

# Инициализируем стандартные скорости из конфигурации
ModbusConnection.STANDARD_BAUDRATES = _config.get('baudrates_to_try', [115200, 57600, 38400, 19200, 9600])
