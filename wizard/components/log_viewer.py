#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Log Viewer Component - Компонент для отображения логов
"""

import sys
import os
from datetime import datetime

from PyQt5.QtWidgets import QTextEdit, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QBrush
from PyQt5.QtCore import Qt

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class LogViewer(QWidget):
    """
    Компонент для отображения логов с цветовой индикацией уровней
    
    Уровни:
    - [INFO] - синий
    - [OK] - зелёный
    - [FAIL] - красный
    - [WARNING] - оранжевый
    - [AUTO] - фиолетовый (для автопоиска)
    - [TEST] - бирюзовый (для тестов)
    """

    def __init__(self, title: str = "Логи", parent=None):
        super().__init__(parent)
        self.title = title
        self.init_ui()

    def init_ui(self):
        """Инициализация UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Заголовок
        header_layout = QHBoxLayout()
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("QLabel { font-weight: bold; font-size: 13px; }")
        header_layout.addWidget(self.title_label)

        # Кнопка очистки
        self.clear_btn = QPushButton("Очистить")
        self.clear_btn.setMaximumWidth(80)
        self.clear_btn.clicked.connect(self.clear)
        header_layout.addWidget(self.clear_btn)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Текстовое поле для логов - увеличенный шрифт
        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Courier", 11))  # Увеличено с 9 до 11
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(self.log_text)

    def log(self, message: str, level: str = "INFO"):
        """
        Добавить сообщение в лог
        
        Args:
            message: Сообщение
            level: Уровень (INFO, OK, FAIL, WARNING, AUTO, TEST)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        # Определяем цвет по уровню
        color_map = {
            "INFO": "#0066cc",      # синий
            "OK": "#28a745",        # зелёный
            "FAIL": "#dc3545",      # красный
            "WARNING": "#ff9800",   # оранжевый
            "AUTO": "#9c27b0",      # фиолетовый
            "TEST": "#00bcd4",      # бирюзовый
            "DEBUG": "#607d8b",     # серый
        }
        
        color = color_map.get(level, "#000000")
        
        # Добавляем текст с цветом
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        
        # Форматируем текст
        format = QTextCharFormat()
        format.setForeground(QBrush(QColor(color)))
        cursor.setCharFormat(format)
        
        cursor.insertText(log_entry)
        self.log_text.setTextCursor(cursor)
        
        # Автоматическая прокрутка вниз
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def info(self, message: str):
        """Лог уровня INFO"""
        self.log(message, "INFO")

    def ok(self, message: str):
        """Лог уровня OK"""
        self.log(message, "OK")

    def fail(self, message: str):
        """Лог уровня FAIL"""
        self.log(message, "FAIL")

    def warning(self, message: str):
        """Лог уровня WARNING"""
        self.log(message, "WARNING")

    def auto(self, message: str):
        """Лог уровня AUTO (автопоиск)"""
        self.log(message, "AUTO")

    def test(self, message: str):
        """Лог уровня TEST (тестирование)"""
        self.log(message, "TEST")

    def debug(self, message: str):
        """Лог уровня DEBUG"""
        self.log(message, "DEBUG")

    def clear(self):
        """Очистить лог"""
        self.log_text.clear()

    def get_text(self) -> str:
        """Получить текст логов"""
        return self.log_text.toPlainText()
