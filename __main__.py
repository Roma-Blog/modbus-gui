#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DVLINK GUI - Главный файл запуска приложения

Выбор интерфейса:
- Новый пошаговый мастер (Wizard)
- Классический интерфейс (ModbusRTUGUI)
"""

import sys
import os

from PyQt5.QtWidgets import QApplication, QMessageBox, QPushButton
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt


def run_wizard_interface(app):
    """Запустить новый интерфейс (Wizard)"""
    from wizard.wizard_main import ConnectionWizard
    
    window = ConnectionWizard()
    window.show()
    return window


def main():
    """Главная функция"""
    try:
        # Создаем приложение
        app = QApplication(sys.argv)
        app.setApplicationName("DVLINK GUI")
        app.setApplicationVersion("2.0")
        app.setStyle("Fusion")

        print("[GUI] Запуск нового интерфейса (Wizard)")
        window = run_wizard_interface(app)

        print("[GUI] Приложение запущено. Для выхода закройте окно.")

        # Запускаем цикл событий
        sys.exit(app.exec_())

    except Exception as e:
        print(f"[GUI] Критическая ошибка при запуске: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
