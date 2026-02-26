#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firmware Display Module
Класс для отображения информации о прошивке и конфигурации
"""

import sys
import os
from PyQt5.QtWidgets import QTextEdit, QVBoxLayout, QGroupBox
from PyQt5.QtGui import QFont

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FirmwareDisplay:
    """Класс для отображения информации о прошивке"""

    def __init__(self, parent=None):
        """
        Инициализация дисплея прошивки

        Args:
            parent: Родительский виджет
        """
        self.parent = parent
        self.firmware_text = None
        self.create_ui()

    def create_ui(self):
        """Создание UI компонента"""
        # Группа информации о прошивке
        firmware_group = QGroupBox("Информация о прошивке")
        firmware_layout = QVBoxLayout(firmware_group)

        self.firmware_text = QTextEdit()
        self.firmware_text.setFont(QFont("Courier", 10))
        self.firmware_text.setReadOnly(True)
        self.firmware_text.setMaximumHeight(200)

        firmware_layout.addWidget(self.firmware_text)

        # Сохраняем ссылку на группу для использования в родительском виджете
        self.firmware_group = firmware_group

    def get_widget(self):
        """Получить виджет для добавления в layout"""
        return self.firmware_group

    def display_firmware_info(self, device_info: dict, baudrate: int):
        """
        Отобразить информацию о прошивке

        Args:
            device_info: Информация об устройстве
            baudrate: Скорость соединения
        """
        if not device_info or not isinstance(device_info, dict):
            self.firmware_text.setPlainText("Информация о прошивке недоступна")
            return

        # Hex формат ответа
        hex_response = device_info.get('raw_hex') or device_info.get('hex_format') or device_info.get('raw_response')
        if not hex_response:
            self.firmware_text.setPlainText("Информация о прошивке недоступна")
            return

        firmware_text = f"Ответ: {hex_response}\n"
        firmware_text += "Версия прошивки:\n"
        firmware_text += "-" * 50 + "\n"

        # Извлекаем device_specific_data если есть
        device_data = device_info.get("device_specific_data", {})

        # Основные поля согласно спецификации
        if "product_id" in device_data:
            pid = device_data["product_id"]
            firmware_text += f"ProductID: {pid.get('value', 'N/A')}\n"

        if "status" in device_data:
            status = device_data["status"]
            firmware_text += f"Status: {status.get('value', 'N/A')}\n"

        if "magic" in device_data:
            magic = device_data["magic"]
            firmware_text += f"Magic: {magic.get('value', 'N/A')}\n"

        if "hardware" in device_data:
            hw = device_data["hardware"]
            firmware_text += f"Hardware: {hw.get('value', 'N/A')}\n"

        if "software" in device_data:
            sw = device_data["software"]
            firmware_text += f"Software: {sw.get('value', 'N/A')}\n"

        if "io_counts" in device_data:
            io = device_data["io_counts"]
            firmware_text += f"DI/DO/AI/AO: {io.get('value', 'N/A')}\n"

        if "ver_status" in device_data:
            vs = device_data["ver_status"]
            firmware_text += f"VerStatus: {vs.get('value', 'N/A')}\n"

        self.firmware_text.setPlainText(firmware_text)

    def display_direct_config_info(self, config: dict, address: int, baudrate: int):
        """
        Отобразить информацию о конфигурации, прочитанной напрямую из регистров

        Args:
            config: Конфигурация
            address: Адрес устройства
            baudrate: Скорость соединения
        """
        if not config:
            self.firmware_text.setPlainText("Информация о конфигурации недоступна")
            return

        config_text = f"Конфигурация устройства (прямое чтение регистров)\n"
        config_text += f"Адрес: {address}, Скорость: {baudrate} baud\n"
        config_text += "=" * 60 + "\n\n"

        config_text += "Прочитанные регистры:\n"
        config_text += "-" * 30 + "\n"
        config_text += f"Регистр 1 (Канал 1): {config.get('channel1', 'N/A')}\n"
        config_text += f"Регистр 2 (Канал 2): {config.get('channel2', 'N/A')}\n"
        config_text += f"Регистр 3 (Modbus скорость): {config.get('modbus_speed_value', 'N/A')} ({config.get('modbus_speed_text', 'N/A')})\n"
        config_text += f"Регистр 6 (Modbus адрес): {config.get('modbus_address', 'N/A')}\n\n"

        config_text += "Интерпретация:\n"
        config_text += "-" * 20 + "\n"
        config_text += f"Количество катушек Канал 1: {config.get('channel1', 'N/A')}\n"
        config_text += f"Количество катушек Канал 2: {config.get('channel2', 'N/A')}\n"
        config_text += f"Скорость Modbus RTU: {config.get('modbus_speed_text', 'N/A')}\n"
        config_text += f"Адрес устройства: {config.get('modbus_address', 'N/A')}\n\n"

        config_text += f"Время чтения: {config.get('timestamp', 'N/A')}"

        self.firmware_text.setPlainText(config_text)

    def clear_display(self):
        """Очистить дисплей"""
        self.firmware_text.setPlainText("")

    def set_text(self, text: str):
        """Установить текст напрямую"""
        self.firmware_text.setPlainText(text)