#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Connection Status Indicator - Индикатор статуса подключения
"""

import sys
import os

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class ConnectionStatusIndicator(QWidget):
    """
    Индикатор статуса подключения с отображением информации
    
    Отображает:
    - Статус подключения (цветной индикатор)
    - Порт
    - Адрес устройства
    - Скорость
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.set_disconnected()

    def init_ui(self):
        """Инициализация UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Индикатор статуса (кружок)
        self.status_indicator = QFrame()
        self.status_indicator.setFixedSize(16, 16)
        self.status_indicator.setStyleSheet("""
            QFrame {
                border-radius: 8px;
                background-color: #dc3545;
            }
        """)
        layout.addWidget(self.status_indicator)

        # Текст статуса
        self.status_label = QLabel("Не подключено")
        self.status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.status_label.setStyleSheet("QLabel { color: #dc3545; }")
        layout.addWidget(self.status_label)

        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setFixedWidth(2)
        separator.setStyleSheet("QFrame { background-color: #ccc; }")
        layout.addWidget(separator)

        # Информация о подключении
        self.info_label = QLabel("Порт: - | Адрес: - | Скорость: -")
        self.info_label.setFont(QFont("Arial", 9))
        self.info_label.setStyleSheet("QLabel { color: #666; }")
        layout.addWidget(self.info_label)

        layout.addStretch()

    def set_connected(self, port: str, address: int, baudrate: int):
        """
        Установить статус "Подключено"
        
        Args:
            port: COM порт
            address: Адрес устройства
            baudrate: Скорость
        """
        self.status_indicator.setStyleSheet("""
            QFrame {
                border-radius: 8px;
                background-color: #28a745;
            }
        """)
        self.status_label.setText("Подключено")
        self.status_label.setStyleSheet("QLabel { color: #28a745; }")
        self.info_label.setText(
            f"Порт: {port} | Адрес: {address} | Скорость: {baudrate} baud"
        )

    def set_connecting(self, message: str = "Подключение..."):
        """
        Установить статус "Подключение"
        
        Args:
            message: Сообщение статуса
        """
        self.status_indicator.setStyleSheet("""
            QFrame {
                border-radius: 8px;
                background-color: #ff9800;
                animation: pulse 1s infinite;
            }
        """)
        self.status_label.setText(message)
        self.status_label.setStyleSheet("QLabel { color: #ff9800; }")
        self.info_label.setText("Порт: - | Адрес: - | Скорость: -")

    def set_disconnected(self):
        """Установить статус 'Не подключено'"""
        self.status_indicator.setStyleSheet("""
            QFrame {
                border-radius: 8px;
                background-color: #dc3545;
            }
        """)
        self.status_label.setText("Не подключено")
        self.status_label.setStyleSheet("QLabel { color: #dc3545; }")
        self.info_label.setText("Порт: - | Адрес: - | Скорость: -")

    def set_searching(self, progress: str = "Поиск устройства..."):
        """
        Установить статус "Поиск устройства"
        
        Args:
            progress: Текст прогресса поиска
        """
        self.status_indicator.setStyleSheet("""
            QFrame {
                border-radius: 8px;
                background-color: #ff9800;
            }
        """)
        self.status_label.setText("Поиск...")
        self.status_label.setStyleSheet("QLabel { color: #ff9800; }")
        self.info_label.setText(progress)
