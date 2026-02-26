#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 1: Welcome - Шаг приветствия
"""

import sys
import os
import webbrowser

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class StepWelcome(QWidget):
    """
    Шаг 1: Приветствие

    Функции:
    - Приветственный текст
    - Список возможностей
    - Кнопка "Открыть инструкцию"
    - Кнопка "Далее"
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Инициализация UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Место для логотипа
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setFixedSize(200, 200)
        self.logo_label.setStyleSheet("""
            QLabel {
                background-color: #ecf0f1;
                border: 2px dashed #bdc3c7;
                border-radius: 10px;
            }
        """)
        self.logo_label.setText("Логотип\n(опционально)")
        self.logo_label.setFont(QFont("Arial", 10))
        self.logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo_label)

        # Заголовок
        title = QLabel("Добро пожаловать в DVLINK GUI")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("QLabel { color: #2c3e50; padding: 10px; }")
        layout.addWidget(title)

        # Подзаголовок
        subtitle = QLabel("Мастер подключения и настройки устройства Modbus RTU")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("QLabel { color: #7f8c8d; padding-bottom: 20px; }")
        layout.addWidget(subtitle)

        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("QFrame { background-color: #bdc3c7; }")
        layout.addWidget(line)

        # Список возможностей
        features_title = QLabel("Этот мастер поможет вам:")
        features_title.setFont(QFont("Arial", 13, QFont.Bold))
        features_title.setStyleSheet("QLabel { color: #2c3e50; padding: 10px 0; }")
        layout.addWidget(features_title)

        features_list = QVBoxLayout()
        features_list.setSpacing(10)

        features = [
            "Подключиться к устройству Modbus RTU через COM порт",
            "Автоматически найти устройство (адрес и скорость)",
            "Прочитать и записать конфигурацию устройства",
            "Протестировать устройство в различных режимах",
        ]

        for text in features:
            feature_layout = QHBoxLayout()
            bullet_label = QLabel("•")
            bullet_label.setFont(QFont("Arial", 16))
            bullet_label.setFixedWidth(20)
            bullet_label.setStyleSheet("QLabel { color: #3498db; }")
            feature_layout.addWidget(bullet_label)

            text_label = QLabel(text)
            text_label.setFont(QFont("Arial", 11))
            text_label.setStyleSheet("QLabel { color: #34495e; padding: 5px; }")
            feature_layout.addWidget(text_label)
            feature_layout.addStretch()

            features_list.addLayout(feature_layout)

        layout.addLayout(features_list)

        # Spacer
        spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer)

        # Инструкция - текстовая ссылка
        instr_layout = QHBoxLayout()
        instr_label = QLabel("Перед началом работы рекомендуется ознакомиться с инструкцией")
        instr_label.setFont(QFont("Arial", 10))
        instr_label.setStyleSheet("QLabel { color: #7f8c8d; }")
        instr_layout.addWidget(instr_label)

        self.instruction_link = QLabel("<a href='#' style='color: #3498db; text-decoration: none; font-weight: bold;'>Открыть инструкцию</a>")
        self.instruction_link.setFont(QFont("Arial", 10))
        self.instruction_link.setOpenExternalLinks(False)
        self.instruction_link.linkActivated.connect(self.open_instruction)
        self.instruction_link.setCursor(Qt.PointingHandCursor)
        instr_layout.addWidget(self.instruction_link)
        layout.addLayout(instr_layout)

        # Spacer
        spacer2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer2)

        # Кнопка "Далее"
        # next_layout = QHBoxLayout()
        # next_layout.addStretch()

        # self.next_btn = QPushButton("Далее")
        # self.next_btn.setFont(QFont("Arial", 12, QFont.Bold))
        # self.next_btn.setMinimumSize(150, 45)
        # self.next_btn.clicked.connect(self.on_next_clicked)
        # self.next_btn.setStyleSheet("""
        #     QPushButton {
        #         background-color: #27ae60;
        #         color: white;
        #         border: none;
        #         padding: 12px 24px;
        #         border-radius: 6px;
        #         font-weight: bold;
        #     }
        #     QPushButton:hover {
        #         background-color: #229954;
        #     }
        #     QPushButton:pressed {
        #         background-color: #1e8449;
        #     }
        # """)
        # next_layout.addWidget(self.next_btn)
        # layout.addLayout(next_layout)

    def open_instruction(self):
        """Открыть инструкцию"""
        # Путь к README
        readme_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "README.md"
        )

        if os.path.exists(readme_path):
            # Открываем файл в браузере
            webbrowser.open(f"file://{readme_path}")
        else:
            # Если README не найден, открываем ссылку на документацию
            webbrowser.open("https://github.com/DVLINK/documentation")

    def on_next_clicked(self):
        """Обработчик нажатия кнопки 'Далее'"""
        # Сигнал будет подключён в wizard_main
        pass

    def cleanup(self):
        """Очистка при уходе с шага"""
        pass

    def set_logo(self, logo_path: str):
        """Установить логотип из файла"""
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
            self.logo_label.setText("")
