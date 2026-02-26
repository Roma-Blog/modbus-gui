#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COM Port Connection Diagnostic Tool
Инструмент диагностики подключения к COM портам для Modbus RTU Scanner
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

print(f"DEBUG: current_dir = {current_dir}")
print(f"DEBUG: shared_dir = {shared_dir}")
print(f"DEBUG: sys.path[:3] = {sys.path[:3]}")

def log(message: str, level: str = "INFO"):
    """Логирование с временными метками"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    # Заменяем Unicode символы на ASCII для совместимости с Windows
    message = message.replace("✓", "[OK]").replace("✗", "[FAIL]").replace("⚠", "[WARN]").replace("❌", "[ERROR]").replace("✅", "[SUCCESS]")
    print(f"[{timestamp}] [{level}] {message}")

def test_serial_import():
    """Тест 1: Проверка импорта модуля serial"""
    log("=== ТЕСТ 1: Проверка импорта serial ===")
    try:
        import serial
        log(f"✓ Модуль serial успешно импортирован: {serial.__version__}")
        return True
    except ImportError as e:
        log(f"✗ Ошибка импорта serial: {e}", "ERROR")
        return False
    except Exception as e:
        log(f"✗ Неожиданная ошибка импорта: {e}", "ERROR")
        return False

def test_list_ports():
    """Тест 2: Проверка сканирования портов"""
    log("=== ТЕСТ 2: Сканирование доступных портов ===")
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()

        log(f"Найдено {len(ports)} COM портов:")
        for port in ports:
            log(f"  - {port.device}: {port.description} ({port.manufacturer or 'Unknown'})")

        if not ports:
            log("⚠ Не найдено ни одного COM порта")
            log("  Возможные причины:")
            log("  - Отсутствуют подключенные устройства")
            log("  - Драйверы не установлены")
            log("  - Недостаточно прав доступа")

        # Добавляем стандартные порты для тестирования
        default_ports = ["COM1", "COM2", "COM3", "COM4", "COM5"]
        test_ports = [p.device for p in ports] + default_ports

        return list(set(test_ports))  # Убираем дубликаты

    except ImportError:
        log("⚠ serial.tools.list_ports недоступен, используем стандартный список", "WARNING")
        return ["COM1", "COM2", "COM3", "COM4", "COM5"]
    except Exception as e:
        log(f"✗ Ошибка сканирования портов: {e}", "ERROR")
        return ["COM1", "COM2", "COM3", "COM4", "COM5"]

def test_port_availability(port: str):
    """Тест 3: Проверка доступности конкретного порта"""
    log(f"=== ТЕСТ 3: Проверка доступности порта {port} ===")
    try:
        import serial

        # Попытка открыть порт
        log(f"Попытка открыть порт {port}...")
        ser = serial.Serial(
            port=port,
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.0
        )

        if ser.is_open:
            log(f"✓ Порт {port} успешно открыт")
            ser.close()
            log(f"✓ Порт {port} успешно закрыт")
            return True
        else:
            log(f"✗ Порт {port} не удалось открыть (is_open=False)")
            return False

    except serial.SerialException as e:
        log(f"✗ SerialException для порта {port}: {e}", "ERROR")
        log("  Возможные причины:", "ERROR")
        log("  - Порт не существует", "ERROR")
        log("  - Порт занят другим процессом", "ERROR")
        log("  - Недостаточно прав доступа", "ERROR")
        return False
    except PermissionError as e:
        log(f"✗ PermissionError для порта {port}: {e}", "ERROR")
        log("  Решение: запустите от имени администратора", "ERROR")
        return False
    except Exception as e:
        log(f"✗ Неожиданная ошибка для порта {port}: {e}", "ERROR")
        return False

def test_modbus_imports():
    """Тест 4: Проверка импортов Modbus модулей"""
    log("=== ТЕСТ 4: Проверка импортов Modbus модулей ===")

    results = {}

    # Тестируем каждый модуль отдельно
    try:
        import shared.modbus_connection
        log("✓ shared.modbus_connection успешно импортирован")
        results["shared.modbus_connection"] = True
    except ImportError as e:
        log(f"✗ Ошибка импорта shared.modbus_connection: {e}", "ERROR")
        results["shared.modbus_connection"] = False
    except Exception as e:
        log(f"✗ Неожиданная ошибка импорта shared.modbus_connection: {e}", "ERROR")
        results["shared.modbus_connection"] = False

    try:
        import shared.modbus_rtu_client
        log("✓ shared.modbus_rtu_client успешно импортирован")
        results["shared.modbus_rtu_client"] = True
    except ImportError as e:
        log(f"✗ Ошибка импорта shared.modbus_rtu_client: {e}", "ERROR")
        results["shared.modbus_rtu_client"] = False
    except Exception as e:
        log(f"✗ Неожиданная ошибка импорта shared.modbus_rtu_client: {e}", "ERROR")
        results["shared.modbus_rtu_client"] = False

    try:
        import shared.device_response_parser_fixed
        log("✓ shared.device_response_parser_fixed успешно импортирован")
        results["shared.device_response_parser_fixed"] = True
    except ImportError as e:
        log(f"✗ Ошибка импорта shared.device_response_parser_fixed: {e}", "ERROR")
        results["shared.device_response_parser_fixed"] = False
    except Exception as e:
        log(f"✗ Неожиданная ошибка импорта shared.device_response_parser_fixed: {e}", "ERROR")
        results["shared.device_response_parser_fixed"] = False

    try:
        import modbus_worker
        log("✓ modbus_worker успешно импортирован")
        results["modbus_worker"] = True
    except ImportError as e:
        log(f"✗ Ошибка импорта modbus_worker: {e}", "ERROR")
        results["modbus_worker"] = False
    except Exception as e:
        log(f"✗ Неожиданная ошибка импорта modbus_worker: {e}", "ERROR")
        results["modbus_worker"] = False

    return results

def test_connection_level(port: str):
    """Тест 5: Проверка уровня Connection"""
    log(f"=== ТЕСТ 5: Тест уровня Connection для порта {port} ===")

    try:
        import shared.modbus_connection as mc
        ModbusConnection = mc.ModbusConnection

        log("Создание ModbusConnection...")
        connection = ModbusConnection(port, 9600)

        log("Попытка подключения...")
        start_time = time.time()
        result = connection.connect()
        end_time = time.time()

        if result:
            log(f"✓ Уровень Connection: подключение успешно ({end_time - start_time:.2f} сек)")
            connection.disconnect()
            log("✓ Уровень Connection: отключение успешно")
            return True
        else:
            log(f"✗ Уровень Connection: подключение неудачно ({end_time - start_time:.2f} сек)")
            return False

    except Exception as e:
        log(f"✗ Ошибка уровня Connection: {e}", "ERROR")
        return False

def test_client_level(port: str, address: int = 1):
    """Тест 6: Проверка уровня Client"""
    log(f"=== ТЕСТ 6: Тест уровня Client для порта {port}, адрес {address} ===")

    try:
        import shared.modbus_rtu_client as mrc
        ModbusRTUClient = mrc.ModbusRTUClient

        log("Создание ModbusRTUClient...")
        client = ModbusRTUClient(port, address, 9600)

        log("Попытка подключения...")
        start_time = time.time()
        result = client.connect()
        end_time = time.time()

        if result:
            log(f"✓ Уровень Client: подключение успешно ({end_time - start_time:.2f} сек)")
            client.disconnect()
            log("✓ Уровень Client: отключение успешно")
            return True
        else:
            log(f"✗ Уровень Client: подключение неудачно ({end_time - start_time:.2f} сек)")
            return False

    except Exception as e:
        log(f"✗ Ошибка уровня Client: {e}", "ERROR")
        return False

def test_worker_level(port: str, address: int = 1):
    """Тест 7: Проверка уровня Worker (без GUI)"""
    log(f"=== ТЕСТ 7: Тест уровня Worker для порта {port}, адрес {address} ===")

    try:
        from modbus_worker import ModbusWorkerThread

        log("Создание ModbusWorkerThread...")
        worker = ModbusWorkerThread(port, address, 9600)

        # Имитируем сигналы (просто функции для тестирования)
        def on_connected(success, message):
            if success:
                log(f"✓ Worker сигнал: {message}")
            else:
                log(f"✗ Worker сигнал: {message}")

        def on_error(error_msg):
            log(f"⚠ Worker ошибка: {error_msg}")

        def on_status(status_msg):
            log(f"[STATUS] {status_msg}")

        # Подключаем сигналы
        worker.connected.connect(on_connected)
        worker.error_occurred.connect(on_error)
        worker.status_updated.connect(on_status)

        log("Запуск worker потока...")
        worker.start()

        # Ждем результат (максимум 5 секунд)
        timeout = 5
        start_time = time.time()

        while worker.isRunning() and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        if worker.isRunning():
            log("⚠ Worker поток не завершился за 5 секунд, принудительное завершение")
            worker.stop()
            worker.wait()

        # Проверяем результат
        if hasattr(worker, 'is_connected') and worker.is_connected:
            log("✓ Уровень Worker: подключение успешно")
            worker.stop()
            worker.wait()
            return True
        else:
            log("✗ Уровень Worker: подключение неудачно")
            return False

    except Exception as e:
        log(f"✗ Ошибка уровня Worker: {e}", "ERROR")
        return False

def run_full_diagnostic(port: str = None, address: int = 1):
    """Запуск полной диагностики"""
    log("=" * 60)
    log("НАЧАЛО ДИАГНОСТИКИ ПОДКЛЮЧЕНИЯ К COM ПОРТУ")
    log("=" * 60)

    # Тест 1: Импорт serial
    if not test_serial_import():
        log("❌ ДИАГНОСТИКА ПРЕРВАНА: проблема с модулем serial", "ERROR")
        return False

    # Тест 2: Сканирование портов
    available_ports = test_list_ports()

    if not available_ports:
        log("❌ ДИАГНОСТИКА ПРЕРВАНА: нет доступных портов для тестирования", "ERROR")
        return False

    # Выбор порта для тестирования
    if port is None:
        port = available_ports[0]
        log(f"Выбран порт для тестирования: {port}")

    if port not in available_ports:
        log(f"⚠ Указанный порт {port} не найден в списке доступных", "WARNING")

    # Тест 3: Доступность порта
    if not test_port_availability(port):
        log(f"⚠ Порт {port} недоступен, но продолжаем тестирование", "WARNING")

    # Тест 4: Импорты Modbus
    import_results = test_modbus_imports()
    failed_imports = [k for k, v in import_results.items() if not v]

    if failed_imports:
        log(f"❌ ДИАГНОСТИКА ПРЕРВАНА: проблемы с импортами: {', '.join(failed_imports)}", "ERROR")
        return False

    # Тест 5: Уровень Connection
    connection_ok = test_connection_level(port)

    # Тест 6: Уровень Client
    client_ok = test_client_level(port, address)

    # Тест 7: Уровень Worker
    worker_ok = test_worker_level(port, address)

    # Итоги
    log("=" * 60)
    log("РЕЗУЛЬТАТЫ ДИАГНОСТИКИ:")
    log(f"  Serial импорт: ✓")
    log(f"  Доступные порты: {len(available_ports)} найдено")
    log(f"  Импорты Modbus: ✓")
    log(f"  Уровень Connection: {'✓' if connection_ok else '✗'}")
    log(f"  Уровень Client: {'✓' if client_ok else '✗'}")
    log(f"  Уровень Worker: {'✓' if worker_ok else '✗'}")

    if connection_ok and client_ok and worker_ok:
        log("✅ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!", "SUCCESS")
        log("Подключение к COM портам должно работать корректно.")
        return True
    else:
        log("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ!", "ERROR")
        log("Рекомендации по устранению:")
        if not connection_ok:
            log("  - Проверьте уровень Connection (serial параметры)")
        if not client_ok:
            log("  - Проверьте уровень Client (ModbusRTUClient)")
        if not worker_ok:
            log("  - Проверьте уровень Worker (ModbusWorkerThread)")
        log("  - Проверьте подключение физического устройства")
        log("  - Проверьте настройки порта в Диспетчере устройств")
        return False

def main():
    """Главная функция"""
    import argparse

    parser = argparse.ArgumentParser(description="Диагностика подключения к COM портам")
    parser.add_argument("--port", help="COM порт для тестирования (например, COM1)")
    parser.add_argument("--address", type=int, default=1, help="Адрес Modbus устройства (1-247)")

    args = parser.parse_args()

    try:
        success = run_full_diagnostic(args.port, args.address)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log("Диагностика прервана пользователем", "WARNING")
        sys.exit(1)
    except Exception as e:
        log(f"Критическая ошибка диагностики: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
