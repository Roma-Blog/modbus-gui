#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI Environment Module
Модуль для проверки доступности графической среды
"""

import sys

def check_gui_environment():
    """Проверяет, доступна ли графическая среда"""
    if sys.platform.startswith('win'):
        # На Windows пытаемся импортировать и создать QApplication
        try:
            from PyQt5.QtWidgets import QApplication, QWidget
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            # Проверяем, можем ли мы создать тестовое окно
            test_widget = QWidget()
            test_widget.show()
            test_widget.hide()
            test_widget.close()
            return True
        except Exception as e:
            print(f"Графическая среда недоступна: {e}")
            print("Используйте веб-интерфейс: python web_interface.py")
            return False
    else:
        # На Linux/Unix проверяем DISPLAY
        import os
        if not os.environ.get('DISPLAY'):
            print("Переменная DISPLAY не установлена.")
            print("GUI приложение требует графической среды.")
            print("Установите переменную DISPLAY или используйте X11 forwarding:")
            print("export DISPLAY=:0")
            print("или используйте веб-интерфейс: python web_interface.py")
            return False
        try:
            from PyQt5.QtWidgets import QApplication
            return True
        except Exception as e:
            print(f"Ошибка импорта PyQt5: {e}")
            print("Установите PyQt5: pip install PyQt5")
            print("или используйте веб-интерфейс: python web_interface.py")
            return False

# Проверяем GUI среду
GUI_AVAILABLE = check_gui_environment()
if not GUI_AVAILABLE:
    print("\n" + "="*50)
    print("РЕШЕНИЕ ПРОБЛЕМЫ:")
    print("GUI приложение не может запуститься в текущей среде.")
    print("Используйте веб-интерфейс вместо этого:")
    print("python web_interface.py")
    print("="*50)
    sys.exit(1)
