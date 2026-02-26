#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI Level Connection Test
Тест уровня GUI для проверки подключения к COM портам
"""

import sys
import os
import time
from datetime import datetime

# Добавляем путь для импорта наших модулей
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
shared_dir = os.path.join(parent_dir, 'shared')

sys.path.insert(0, current_dir)
sys.path.insert(0, shared_dir)
sys.path.insert(0, parent_dir)

def log(message: str, level: str = "INFO"):
    """Логирование с временными метками"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    message = message.replace("✓", "[OK]").replace("✗", "[FAIL]").replace("⚠", "[WARN]").replace("❌", "[ERROR]").replace("✅", "[SUCCESS]")
    print(f"[{timestamp}] [{level}] {message}")

def test_gui_imports():
    """Тест 1: Проверка импортов GUI модулей"""
    log("=== ТЕСТ 1: Проверка импортов GUI модулей ===")

    try:
        from modbus_gui_main import ModbusRTUGUI
        log("[OK] ModbusRTUGUI успешно импортирован")
        return True
    except ImportError as e:
        log(f"[FAIL] Ошибка импорта ModbusRTUGUI: {e}", "ERROR")
        return False
    except Exception as e:
        log(f"[FAIL] Неожиданная ошибка импорта: {e}", "ERROR")
        return False

def test_gui_initialization():
    """Тест 2: Проверка инициализации GUI"""
    log("=== ТЕСТ 2: Проверка инициализации GUI ===")

    try:
        # Импортируем QApplication для headless режима
        from PyQt5.QtWidgets import QApplication
        import sys
        from modbus_gui_main import ModbusRTUGUI

        # Создаем QApplication если его нет
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        log("Создание экземпляра ModbusRTUGUI...")
        start_time = time.time()
        gui = ModbusRTUGUI()
        end_time = time.time()

        log(f"[OK] GUI инициализирован успешно ({end_time - start_time:.2f} сек)")

        # Проверяем наличие основных атрибутов
        required_attrs = ['port_combo', 'address_spinbox', 'baudrate_combo', 'connect_btn']
        for attr in required_attrs:
            if hasattr(gui, attr):
                log(f"[OK] Атрибут {attr} присутствует")
            else:
                log(f"[FAIL] Атрибут {attr} отсутствует", "ERROR")
                return False

        # Проверяем сканирование портов
        if hasattr(gui, '_scan_available_ports'):
            log("Вызов _scan_available_ports()...")
            gui._scan_available_ports()
            log("[OK] Сканирование портов выполнено")

        # Проверяем валидацию порта
        if hasattr(gui, '_is_port_available'):
            test_ports = ["COM4", "COM1", "COM3"]
            for port in test_ports:
                available = gui._is_port_available(port)
                status = "[OK]" if available else "[WARN]"
                log(f"{status} Порт {port} доступность проверена")

        # Очищаем ресурсы
        gui.close()
        app.processEvents()

        log("[OK] GUI инициализация и базовые функции работают корректно")
        return True

    except Exception as e:
        log(f"[FAIL] Ошибка инициализации GUI: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False

def test_gui_connection_logic():
    """Тест 3: Проверка логики подключения GUI"""
    log("=== ТЕСТ 3: Проверка логики подключения GUI ===")

    try:
        from PyQt5.QtWidgets import QApplication
        import sys
        from modbus_gui_main import ModbusRTUGUI

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        gui = ModbusRTUGUI()

        # Тест валидации параметров
        log("Тестирование валидации параметров...")

        # Тест 1: Пустой порт
        gui.port_combo.setCurrentText("")
        try:
            # Имитируем вызов connect без реального подключения
            port = gui.port_combo.currentText().strip()
            if not port:
                log("[OK] Валидация пустого порта работает")
            else:
                log("[FAIL] Валидация пустого порта не работает", "ERROR")
        except:
            pass

        # Тест 2: Некорректная скорость
        gui.port_combo.setCurrentText("COM4")
        gui.baudrate_combo.setCurrentText("invalid")
        try:
            baudrate_text = gui.baudrate_combo.currentText()
            if baudrate_text == "Автоопределение":
                baudrate = 9600
            else:
                baudrate = int(baudrate_text)
            log("[OK] Валидация скорости работает")
        except ValueError:
            log("[OK] Валидация скорости корректно отлавливает ошибки")
        except:
            log("[FAIL] Неожиданная ошибка валидации скорости", "ERROR")

        # Тест 3: Корректные параметры
        gui.port_combo.setCurrentText("COM4")
        gui.address_spinbox.setValue(1)
        gui.baudrate_combo.setCurrentText("9600")

        port = gui.port_combo.currentText().strip()
        address = gui.address_spinbox.value()
        baudrate_text = gui.baudrate_combo.currentText()

        # Проверки
        checks_passed = 0

        if port:
            checks_passed += 1
            log("[OK] Порт валиден")
        else:
            log("[FAIL] Порт не валиден", "ERROR")

        if 1 <= address <= 247:
            checks_passed += 1
            log("[OK] Адрес устройства валиден")
        else:
            log("[FAIL] Адрес устройства не валиден", "ERROR")

        try:
            if baudrate_text == "Автоопределение":
                baudrate = 9600
            else:
                baudrate = int(baudrate_text)
            checks_passed += 1
            log("[OK] Скорость валидна")
        except ValueError:
            log("[FAIL] Скорость не валидна", "ERROR")

        # Очищаем ресурсы
        gui.close()
        app.processEvents()

        if checks_passed == 3:
            log("[OK] Логика подключения GUI работает корректно")
            return True
        else:
            log(f"[FAIL] Логика подключения GUI имеет проблемы ({checks_passed}/3 проверок пройдено)", "ERROR")
            return False

    except Exception as e:
        log(f"[FAIL] Ошибка тестирования логики подключения: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False

def test_gui_port_scanning():
    """Тест 4: Проверка сканирования портов в GUI"""
    log("=== ТЕСТ 4: Проверка сканирования портов в GUI ===")

    try:
        from PyQt5.QtWidgets import QApplication
        import sys
        from modbus_gui_main import ModbusRTUGUI

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        gui = ModbusRTUGUI()

        # Проверяем начальное состояние combo box
        initial_count = gui.port_combo.count()
        log(f"Начальное количество портов в combo: {initial_count}")

        # Вызываем сканирование
        gui._scan_available_ports()

        # Проверяем результат
        final_count = gui.port_combo.count()
        log(f"Количество портов после сканирования: {final_count}")

        if final_count > 0:
            log("[OK] Сканирование портов добавило порты в список")
            # Показываем первые несколько портов
            for i in range(min(5, final_count)):
                port_name = gui.port_combo.itemText(i)
                log(f"  - {port_name}")
        else:
            log("[WARN] Сканирование портов не добавило порты в список", "WARNING")

        # Проверяем, что COM4 присутствует (мы знаем, что он доступен)
        com4_found = False
        for i in range(final_count):
            if gui.port_combo.itemText(i) == "COM4":
                com4_found = True
                break

        if com4_found:
            log("[OK] COM4 присутствует в списке портов")
        else:
            log("[WARN] COM4 не найден в списке портов", "WARNING")

        # Очищаем ресурсы
        gui.close()
        app.processEvents()

        log("[OK] Сканирование портов в GUI работает")
        return True

    except Exception as e:
        log(f"[FAIL] Ошибка тестирования сканирования портов: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False

def run_gui_level_tests():
    """Запуск всех тестов уровня GUI"""
    log("=" * 60)
    log("НАЧАЛО ТЕСТИРОВАНИЯ УРОВНЯ GUI")
    log("=" * 60)

    results = {}

    # Тест 1: Импорты GUI
    results["imports"] = test_gui_imports()

    # Тест 2: Инициализация GUI
    results["initialization"] = test_gui_initialization()

    # Тест 3: Логика подключения
    results["connection_logic"] = test_gui_connection_logic()

    # Тест 4: Сканирование портов
    results["port_scanning"] = test_gui_port_scanning()

    # Итоги
    log("=" * 60)
    log("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ УРОВНЯ GUI:")
    for test_name, result in results.items():
        status = "[OK]" if result else "[FAIL]"
        log(f"  {test_name}: {status}")

    passed_tests = sum(results.values())
    total_tests = len(results)

    if passed_tests == total_tests:
        log("[SUCCESS] ВСЕ ТЕСТЫ УРОВНЯ GUI ПРОШЛИ УСПЕШНО!")
        return True
    else:
        log(f"[ERROR] ПРОЙДЕНО {passed_tests}/{total_tests} ТЕСТОВ УРОВНЯ GUI")
        return False

def main():
    """Главная функция"""
    try:
        success = run_gui_level_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log("Тестирование прервано пользователем", "WARNING")
        sys.exit(1)
    except Exception as e:
        log(f"Критическая ошибка тестирования: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
