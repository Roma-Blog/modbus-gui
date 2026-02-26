#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config Manager Module
Класс для управления конфигурацией устройства Modbus
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import sys
import os

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import (
    REGISTER_ADDRESSES, MODBUS_SPEED_MAP, MODBUS_SPEED_REVERSE_MAP,
    CAN_SPEED_MAP, CAN_SPEED_REVERSE_MAP, LIMITS
)


class ConfigManager:
    """Класс для управления конфигурацией устройства"""

    def __init__(self, worker_thread):
        """
        Инициализация менеджера конфигурации

        Args:
            worker_thread: Экземпляр ModbusWorkerThread
        """
        self.worker_thread = worker_thread
        self.config_data = {}

    def read_device_config(self, max_retries=3) -> Optional[Dict[str, Any]]:
        """
        Прочитать конфигурацию устройства с повторными попытками

        Args:
            max_retries: Максимальное количество попыток чтения

        Returns:
            Dict с данными конфигурации или None при ошибке
        """
        if not self.worker_thread or not self.worker_thread.is_connected:
            return None

        for attempt in range(max_retries):
            print(f"[CONFIG] Попытка чтения конфигурации {attempt + 1}/{max_retries}...")
            
            config = {}
            read_success = True
            
            try:
                # Читаем регистры каналов (1-2) - может не поддерживаться
                print(f"[CONFIG] Чтение регистров каналов (адрес={REGISTER_ADDRESSES['CHANNELS']})...")
                try:
                    channels_data = self.worker_thread.read_holding_registers(
                        REGISTER_ADDRESSES["CHANNELS"], 2
                    )
                    print(f"[CONFIG] Результат чтения каналов: {channels_data}")

                    # Обрабатываем данные каналов
                    if (channels_data and "holding_registers" in channels_data and
                        len(channels_data["holding_registers"]) >= 2):
                        config["channel1"] = channels_data["holding_registers"][0]
                        config["channel2"] = channels_data["holding_registers"][1]
                        print(f"[CONFIG] Каналы: channel1={config['channel1']}, channel2={config['channel2']}")
                    else:
                        print(f"[CONFIG] НЕ УДАЛОСЬ прочитать каналы")
                        read_success = False  # Повторная попытка!
                except Exception as e:
                    print(f"[CONFIG] Ошибка чтения каналов: {e}")
                    read_success = False  # Повторная попытка!

                # Обрабатываем скорость Modbus
                print(f"[CONFIG] Чтение скорости Modbus...")
                try:
                    modbus_speed_data = self.worker_thread.read_holding_registers(
                        REGISTER_ADDRESSES["MODBUS_SPEED"], 1
                    )
                    print(f"[CONFIG] Результат чтения скорости: {modbus_speed_data}")
                    
                    if (modbus_speed_data and "holding_registers" in modbus_speed_data and
                        len(modbus_speed_data["holding_registers"]) >= 1):
                        speed_value = modbus_speed_data["holding_registers"][0]
                        config["modbus_speed_value"] = speed_value
                        config["modbus_speed_text"] = MODBUS_SPEED_MAP.get(speed_value, "9600")
                    else:
                        print(f"[CONFIG] НЕ УДАЛОСЬ прочитать скорость")
                        read_success = False
                except Exception as e:
                    print(f"[CONFIG] Ошибка чтения скорости: {e}")
                    read_success = False
                
                # Обрабатываем адрес Modbus
                print(f"[CONFIG] Чтение адреса Modbus...")
                try:
                    modbus_address_data = self.worker_thread.read_holding_registers(
                        REGISTER_ADDRESSES["MODBUS_ADDRESS"], 1
                    )
                    print(f"[CONFIG] Результат чтения адреса: {modbus_address_data}")
                    
                    if (modbus_address_data and "holding_registers" in modbus_address_data and
                        len(modbus_address_data["holding_registers"]) >= 1):
                        address_value = modbus_address_data["holding_registers"][0]
                        if LIMITS["MIN_DEVICE_ADDRESS"] <= address_value <= LIMITS["MAX_DEVICE_ADDRESS"]:
                            config["modbus_address"] = address_value
                        else:
                            print(f"[CONFIG] Неверный адрес устройства: {address_value}")
                            read_success = False
                    else:
                        print(f"[CONFIG] НЕ УДАЛОСЬ прочитать адрес")
                        read_success = False
                except Exception as e:
                    print(f"[CONFIG] Ошибка чтения адреса: {e}")
                    read_success = False

                # Читаем CAN параметры (регистры 10-11)
                print(f"[CONFIG] Чтение CAN параметров...")
                try:
                    can_data = self.worker_thread.read_holding_registers(
                        REGISTER_ADDRESSES["CAN_PARAMS"], 2
                    )
                    print(f"[CONFIG] Результат чтения CAN: {can_data}")
                    
                    # Обрабатываем CAN параметры
                    if (can_data and "holding_registers" in can_data and
                        len(can_data["holding_registers"]) >= 2):
                        can_speed_value = can_data["holding_registers"][0]
                        can_address_value = can_data["holding_registers"][1]

                        config["can_speed_value"] = can_speed_value
                        config["can_speed_text"] = CAN_SPEED_MAP.get(can_speed_value, "1000K")

                        if LIMITS["MIN_CAN_ADDRESS"] <= can_address_value <= LIMITS["MAX_CAN_ADDRESS"]:
                            config["can_address"] = can_address_value
                            config["can_address_text"] = str(can_address_value)
                        else:
                            print(f"[CONFIG] Неверный CAN адрес: {can_address_value}")
                            read_success = False
                    else:
                        print(f"[CONFIG] НЕ УДАЛОСЬ прочитать CAN параметры")
                        read_success = False
                except Exception as e:
                    print(f"[CONFIG] Ошибка чтения CAN: {e}")
                    read_success = False

                # Если все данные прочитаны успешно - возвращаем конфигурацию
                if read_success:
                    config["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.config_data = config
                    print(f"[CONFIG] Конфигурация успешно прочитана: {config}")
                    return config
                else:
                    print(f"[CONFIG] Попытка {attempt + 1} неудачна - некоторые данные не прочитаны")
                    if attempt < max_retries - 1:
                        print(f"[CONFIG] Повторная попытка через 1 секунду...")
                        import time
                        time.sleep(1)

            except Exception as e:
                print(f"[CONFIG] Ошибка чтения конфигурации: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"[CONFIG] Повторная попытка через 1 секунду...")
                    import time
                    time.sleep(1)

        # Все попытки исчерпаны
        print(f"[CONFIG] Все {max_retries} попыток исчерпаны - возвращаем что есть")
        if config:
            # Если каналы не прочитаны - устанавливаем 0
            if "channel1" not in config:
                config["channel1"] = 0
            if "channel2" not in config:
                config["channel2"] = 0
                
            config["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.config_data = config
            return config
        return None

    def write_device_config(self, config: Dict[str, Any]) -> bool:
        """
        Записать конфигурацию на устройство

        Args:
            config: Словарь с данными конфигурации

        Returns:
            bool: True при успехе, False при ошибке
        """
        if not self.worker_thread or not self.worker_thread.is_connected:
            return False

        try:
            success_count = 0
            total_operations = 0

            # Записываем каналы (регистры 1-2)
            if "channel1" in config and "channel2" in config:
                channel_values = [config["channel1"], config["channel2"]]
                result = self.worker_thread.write_holding_registers(
                    REGISTER_ADDRESSES["CHANNELS"], channel_values
                )
                if result and result.get("status") == "success":
                    success_count += 1
                total_operations += 1

            # Записываем скорость Modbus (регистр 3)
            if "modbus_speed_text" in config:
                speed_value = MODBUS_SPEED_REVERSE_MAP.get(config["modbus_speed_text"], 2)
                result = self.worker_thread.write_holding_registers(
                    REGISTER_ADDRESSES["MODBUS_SPEED"], [speed_value]
                )
                if result and result.get("status") == "success":
                    success_count += 1
                total_operations += 1

            # Записываем адрес Modbus (регистр 6)
            if "modbus_address" in config:
                result = self.worker_thread.write_holding_registers(
                    REGISTER_ADDRESSES["MODBUS_ADDRESS"], [config["modbus_address"]]
                )
                if result and result.get("status") == "success":
                    success_count += 1
                total_operations += 1

            # Записываем CAN параметры (регистры 10-11)
            if "can_speed_text" in config and "can_address" in config:
                can_speed_value = CAN_SPEED_REVERSE_MAP.get(config["can_speed_text"], 7)
                can_address_value = config["can_address"]
                can_values = [can_speed_value, can_address_value]
                result = self.worker_thread.write_holding_registers(
                    REGISTER_ADDRESSES["CAN_PARAMS"], can_values
                )
                if result and result.get("status") == "success":
                    success_count += 1
                total_operations += 1

            return success_count == total_operations

        except Exception as e:
            print(f"[CONFIG] Ошибка записи конфигурации: {str(e)}")
            return False

    def read_modbus_rtu_config_from_device(self) -> Optional[Dict[str, Any]]:
        """
        Прочитать только Modbus RTU параметры

        Returns:
            Dict с Modbus RTU параметрами или None
        """
        if not self.worker_thread or not self.worker_thread.is_connected:
            return None

        try:
            # Читаем регистр 3 (скорость Modbus)
            speed_data = self.worker_thread.read_holding_registers(
                REGISTER_ADDRESSES["MODBUS_SPEED"], 1
            )

            # Читаем регистр 6 (адрес Modbus)
            address_data = self.worker_thread.read_holding_registers(
                REGISTER_ADDRESSES["MODBUS_ADDRESS"], 1
            )

            config = {}

            if (speed_data and "holding_registers" in speed_data and
                len(speed_data["holding_registers"]) >= 1):
                speed_value = speed_data["holding_registers"][0]
                config["modbus_speed_value"] = speed_value
                config["modbus_speed_text"] = MODBUS_SPEED_MAP.get(speed_value, "9600")

            if (address_data and "holding_registers" in address_data and
                len(address_data["holding_registers"]) >= 1):
                address_value = address_data["holding_registers"][0]
                if LIMITS["MIN_DEVICE_ADDRESS"] <= address_value <= LIMITS["MAX_DEVICE_ADDRESS"]:
                    config["modbus_address"] = address_value

            return config

        except Exception as e:
            print(f"[CONFIG] Ошибка чтения Modbus RTU параметров: {str(e)}")
            return None

    def get_config_summary(self) -> str:
        """
        Получить текстовое summary конфигурации

        Returns:
            str: Текстовое описание конфигурации
        """
        if not self.config_data:
            return "Конфигурация не загружена"

        summary = "Текущая конфигурация:\n"
        summary += f"Канал 1: {self.config_data.get('channel1', 'N/A')} катушек\n"
        summary += f"Канал 2: {self.config_data.get('channel2', 'N/A')} катушек\n"
        summary += f"Modbus скорость: {self.config_data.get('modbus_speed_text', 'N/A')}\n"
        summary += f"Modbus адрес: {self.config_data.get('modbus_address', 'N/A')}\n"
        summary += f"CAN скорость: {self.config_data.get('can_speed_text', 'N/A')}\n"
        summary += f"CAN адрес: {self.config_data.get('can_address', 'N/A')}\n"
        summary += f"Время чтения: {self.config_data.get('timestamp', 'N/A')}"

        return summary

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """
        Валидировать конфигурацию

        Args:
            config: Словарь с данными конфигурации

        Returns:
            List[str]: Список ошибок валидации
        """
        errors = []

        # Проверяем каналы
        for channel in ["channel1", "channel2"]:
            if channel in config:
                value = config[channel]
                if not isinstance(value, int) or value < 0 or value > LIMITS["MAX_COILS_PER_CHANNEL"]:
                    errors.append(f"{channel}: значение должно быть от 0 до {LIMITS['MAX_COILS_PER_CHANNEL']}")

        # Проверяем Modbus адрес
        if "modbus_address" in config:
            addr = config["modbus_address"]
            if not isinstance(addr, int) or not (LIMITS["MIN_DEVICE_ADDRESS"] <= addr <= LIMITS["MAX_DEVICE_ADDRESS"]):
                errors.append(f"Modbus адрес: должен быть от {LIMITS['MIN_DEVICE_ADDRESS']} до {LIMITS['MAX_DEVICE_ADDRESS']}")

        # Проверяем CAN адрес
        if "can_address" in config:
            addr = config["can_address"]
            if not isinstance(addr, int) or not (LIMITS["MIN_CAN_ADDRESS"] <= addr <= LIMITS["MAX_CAN_ADDRESS"]):
                errors.append(f"CAN адрес: должен быть от {LIMITS['MIN_CAN_ADDRESS']} до {LIMITS['MAX_CAN_ADDRESS']}")

        return errors