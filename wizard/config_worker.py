#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config Worker Thread - Поток для операций конфигурации
"""

import sys
import os
import time

from PyQt5.QtCore import QThread, pyqtSignal

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ConfigReadWorker(QThread):
    """Поток для чтения конфигурации"""

    finished = pyqtSignal(dict)  # Конфигурация
    error = pyqtSignal(str)  # Ошибка
    progress = pyqtSignal(str)  # Статус

    def __init__(self, config_manager, worker_thread):
        super().__init__()
        self.config_manager = config_manager
        self.worker_thread = worker_thread

    def run(self):
        """Выполнить чтение конфигурации"""
        try:
            self.progress.emit("Чтение регистров устройства...")

            # Читаем конфигурацию
            config = self.config_manager.read_device_config()
            
            # Логируем для отладки
            print(f"[CONFIG_READ] Результат чтения: {config}")

            if config:
                self.progress.emit("Чтение информации о прошивке...")
                # Читаем device_info
                device_info = self.worker_thread.read_device_info()
                config['device_info'] = device_info
                self.finished.emit(config)
            else:
                self.error.emit("Не удалось прочитать конфигурацию")

        except Exception as e:
            self.error.emit(f"Ошибка чтения: {str(e)}")


class ConfigWriteWorker(QThread):
    """Поток для записи конфигурации"""

    finished = pyqtSignal(bool)  # Успех
    error = pyqtSignal(str)  # Ошибка
    progress = pyqtSignal(str)  # Статус

    def __init__(self, config_manager, config: dict):
        super().__init__()
        self.config_manager = config_manager
        self.config = config

    def run(self):
        """Выполнить запись конфигурации"""
        try:
            # Записываем каналы (регистры 1-2)
            self.progress.emit("Запись каналов...")
            self._write_channels()
            time.sleep(0.3)  # Задержка между записями

            # Записываем скорость Modbus (регистр 3)
            self.progress.emit("Запись скорости Modbus...")
            self._write_modbus_speed()
            time.sleep(0.3)

            # Записываем CAN параметры (регистры 10-11)
            self.progress.emit("Запись CAN параметров...")
            self._write_can_params()
            time.sleep(0.3)

            # Записываем адрес Modbus ПОСЛЕДНИМ (регистр 6)
            # После этого устройство может перестать отвечать
            self.progress.emit("Запись адреса Modbus...")
            self._write_modbus_address()
            
            # Даём устройству время на применение настроек
            time.sleep(0.5)

            self.progress.emit("Конфигурация записана")
            self.finished.emit(True)

        except Exception as e:
            self.error.emit(f"Ошибка записи: {str(e)}")

    def _write_channels(self):
        """Записать конфигурацию каналов"""
        if "channel1" in self.config and "channel2" in self.config:
            from constants import REGISTER_ADDRESSES
            values = [self.config["channel1"], self.config["channel2"]]
            self.config_manager.worker_thread.write_holding_registers(
                REGISTER_ADDRESSES["CHANNELS"], values
            )

    def _write_modbus_speed(self):
        """Записать скорость Modbus"""
        if "modbus_speed_text" in self.config:
            from constants import REGISTER_ADDRESSES, MODBUS_SPEED_REVERSE_MAP
            speed_value = MODBUS_SPEED_REVERSE_MAP.get(self.config["modbus_speed_text"], 2)
            self.config_manager.worker_thread.write_holding_registers(
                REGISTER_ADDRESSES["MODBUS_SPEED"], [speed_value]
            )

    def _write_can_params(self):
        """Записать CAN параметры"""
        if "can_speed_text" in self.config and "can_address" in self.config:
            from constants import REGISTER_ADDRESSES, CAN_SPEED_REVERSE_MAP
            can_speed_value = CAN_SPEED_REVERSE_MAP.get(self.config["can_speed_text"], 7)
            can_address_value = self.config["can_address"]
            values = [can_speed_value, can_address_value]
            self.config_manager.worker_thread.write_holding_registers(
                REGISTER_ADDRESSES["CAN_PARAMS"], values
            )

    def _write_modbus_address(self):
        """Записать адрес Modbus (последним, устройство может перестать отвечать)"""
        if "modbus_address" in self.config:
            from constants import REGISTER_ADDRESSES
            try:
                self.config_manager.worker_thread.write_holding_registers(
                    REGISTER_ADDRESSES["MODBUS_ADDRESS"], [self.config["modbus_address"]]
                )
            except:
                # Ошибка при записи адреса - это нормально, устройство могло перезагрузиться
                pass
