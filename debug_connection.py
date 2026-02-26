#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug Connection Tool
Инструмент для отладки подключения к COM портам
"""

import sys
import os
import serial
import time
from datetime import datetime

# Импортируем модули из локальной папки core

def log(message: str, level: str = "INFO"):
    """Логирование с временными метками"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    message = message.replace("✓", "[OK]").replace("✗", "[FAIL]").replace("⚠", "[WARN]").replace("❌", "[ERROR]").replace("✅", "[SUCCESS]")
    print(f"[{timestamp}] [{level}] {message}")

def test_raw_serial_connection(port: str, baudrate: int = 9600):
    """Тест 1: Прямое подключение через serial.Serial"""
    log(f"=== ТЕСТ 1: Прямое подключение к {port} ===")

    try:
        log(f"Создание serial.Serial(port='{port}', baudrate={baudrate}, ...)")

        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.0
        )

        log(f"Объект serial создан: {ser}")
        log(f"ser.is_open: {ser.is_open}")
        log(f"ser.port: {ser.port}")
        log(f"ser.baudrate: {ser.baudrate}")

        if ser.is_open:
            log("[OK] Порт успешно открыт")
            time.sleep(0.1)  # Небольшая пауза
            ser.close()
            log("[OK] Порт успешно закрыт")
            return True
        else:
            log("[FAIL] Порт не открыт (is_open=False)")
            ser.close()
            return False

    except serial.SerialException as e:
        log(f"[FAIL] SerialException: {e}", "ERROR")
        return False
    except PermissionError as e:
        log(f"[FAIL] PermissionError: {e}", "ERROR")
        return False
    except Exception as e:
        log(f"[FAIL] Неожиданная ошибка: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False

def test_modbus_connection_level(port: str, baudrate: int = 9600):
    """Тест 2: Подключение через ModbusConnection"""
    log(f"=== ТЕСТ 2: ModbusConnection к {port} ===")

    try:
        from core.modbus_connection import ModbusConnection

        log("Создание ModbusConnection...")
        connection = ModbusConnection(port, baudrate)

        log("Вызов connection.connect()...")
        start_time = time.time()
        result = connection.connect()
        end_time = time.time()

        log(f"Результат: {result} (время: {end_time - start_time:.2f} сек)")

        if result:
            log("[OK] ModbusConnection.connect() вернул True")
            if connection.connection:
                log(f"[OK] connection.connection установлен: {connection.connection}")
                log(f"[OK] connection.connection.is_open: {connection.connection.is_open}")
            else:
                log("[WARN] connection.connection is None")
            connection.disconnect()
            log("[OK] ModbusConnection.disconnect() выполнен")
            return True
        else:
            log("[FAIL] ModbusConnection.connect() вернул False")
            return False

    except Exception as e:
        log(f"[FAIL] Ошибка в ModbusConnection: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False

def test_modbus_client_level(port: str, address: int = 1, baudrate: int = 9600):
    """Тест 3: Подключение через ModbusRTUClient"""
    log(f"=== ТЕСТ 3: ModbusRTUClient к {port}, адрес {address} ===")

    try:
        from core.modbus_rtu_client import ModbusRTUClient

        log("Создание ModbusRTUClient...")
        client = ModbusRTUClient(port, address, baudrate)

        log("Вызов client.connect()...")
        start_time = time.time()
        result = client.connect()
        end_time = time.time()

        log(f"Результат: {result} (время: {end_time - start_time:.2f} сек)")

        if result:
            log("[OK] ModbusRTUClient.connect() вернул True")
            if client.connection and client.connection.connection:
                log(f"[OK] client.connection.connection установлен: {client.connection.connection}")
                log(f"[OK] client.connection.connection.is_open: {client.connection.connection.is_open}")
            else:
                log("[WARN] client.connection или client.connection.connection is None")
            client.disconnect()
            log("[OK] ModbusRTUClient.disconnect() выполнен")
            return True
        else:
            log("[FAIL] ModbusRTUClient.connect() вернул False")
            return False

    except Exception as e:
        log(f"[FAIL] Ошибка в ModbusRTUClient: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False

def test_worker_thread_level(port: str, address: int = 1, baudrate: int = 9600):
    """Тест 4: Подключение через ModbusWorkerThread"""
    log(f"=== ТЕСТ 4: ModbusWorkerThread к {port}, адрес {address} ===")

    try:
        from modbus_worker import ModbusWorkerThread
        from PyQt5.QtWidgets import QApplication
        import sys

        # Создаем QApplication для обработки сигналов Qt
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        log("Создание ModbusWorkerThread...")
        worker = ModbusWorkerThread(port, address, baudrate)

        # Переменные для сигналов
        connected_result = None
        connected_message = None
        error_message = None
        status_messages = []

        def on_connected(success, message):
            nonlocal connected_result, connected_message
            connected_result = success
            connected_message = message
            log(f"Сигнал connected: success={success}, message='{message}'")

        def on_error(err_msg):
            nonlocal error_message
            error_message = err_msg
            log(f"Сигнал error: '{err_msg}'")

        def on_status(status_msg):
            status_messages.append(status_msg)
            log(f"Сигнал status: '{status_msg}'")

        # Подключаем сигналы
        worker.connected.connect(on_connected)
        worker.error_occurred.connect(on_error)
        worker.status_updated.connect(on_status)

        log("Запуск worker.start()...")
        worker.start()

        # Ждем результат с обработкой Qt events
        timeout = 3
        start_time = time.time()
        signal_received = False

        while worker.isRunning() and (time.time() - start_time) < timeout and not signal_received:
            # Обрабатываем Qt events для получения сигналов
            app.processEvents()
            time.sleep(0.01)  # Очень короткие интервалы

            # Проверяем, получили ли мы сигнал connected
            if connected_result is not None:
                signal_received = True
                log(f"[OK] Сигнал connected получен: {connected_result}")
                break

        # Даем еще немного времени на завершение
        if worker.isRunning():
            time.sleep(0.1)
            app.processEvents()

        if worker.isRunning():
            log("[WARN] Worker все еще работает, принудительное завершение")
            worker.stop()
            worker.wait()

        log(f"connected_result: {connected_result}")
        log(f"connected_message: {connected_message}")
        log(f"error_message: {error_message}")
        log(f"status_messages: {status_messages}")

        # Очищаем ресурсы QApplication
        app.processEvents()

        if connected_result is True:
            log("[OK] Worker успешно подключился")
            return True
        elif connected_result is False:
            log("[FAIL] Worker вернул ошибку подключения")
            return False
        else:
            log("[FAIL] Worker не вернул результат подключения (сигнал не получен)")
            return False

    except Exception as e:
        log(f"[FAIL] Ошибка в ModbusWorkerThread: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False

def run_debug_diagnostic(port: str, address: int = 1, baudrate: int = 9600):
    """Запуск полной отладочной диагностики"""
    log("=" * 70)
    log(f"ОТЛАДОЧНАЯ ДИАГНОСТИКА ПОДКЛЮЧЕНИЯ К {port}")
    log("=" * 70)

    results = {}

    # Тест 1: Raw serial
    results["raw_serial"] = test_raw_serial_connection(port, baudrate)
    time.sleep(0.5)  # Пауза между тестами

    # Тест 2: ModbusConnection
    results["modbus_connection"] = test_modbus_connection_level(port, baudrate)
    time.sleep(0.5)

    # Тест 3: ModbusRTUClient
    results["modbus_client"] = test_modbus_client_level(port, address, baudrate)
    time.sleep(0.5)

    # Тест 4: ModbusWorkerThread
    results["worker_thread"] = test_worker_thread_level(port, address, baudrate)

    # Итоги
    log("=" * 70)
    log("РЕЗУЛЬТАТЫ ОТЛАДОЧНОЙ ДИАГНОСТИКИ:")
    for test_name, result in results.items():
        status = "[OK]" if result else "[FAIL]"
        log(f"  {test_name}: {status}")

    passed_tests = sum(results.values())
    total_tests = len(results)

    log(f"\nПРОЙДЕНО: {passed_tests}/{total_tests} ТЕСТОВ")

    if passed_tests == total_tests:
        log("[SUCCESS] ВСЕ УРОВНИ РАБОТАЮТ КОРРЕКТНО")
    elif passed_tests >= 2:
        log("[WARN] ПРОБЛЕМА НА ВЫСШИХ УРОВНЯХ (Worker/Client)")
        log("Рекомендации:")
        log("- Проверьте, не занят ли порт другим процессом")
        log("- Попробуйте перезагрузить систему")
        log("- Проверьте подключение физического устройства")
    else:
        log("[ERROR] КРИТИЧЕСКИЕ ПРОБЛЕМЫ НА НИЗКИХ УРОВНЯХ")
        log("Рекомендации:")
        log("- Проверьте права доступа к COM портам")
        log("- Убедитесь, что порт существует")
        log("- Проверьте драйверы устройства")

    return results

def main():
    """Главная функция"""
    import argparse

    parser = argparse.ArgumentParser(description="Отладка подключения к COM портам")
    parser.add_argument("--port", default="COM4", help="COM порт для тестирования")
    parser.add_argument("--address", type=int, default=1, help="Адрес Modbus устройства")
    parser.add_argument("--baudrate", type=int, default=9600, help="Скорость подключения")

    args = parser.parse_args()

    try:
        run_debug_diagnostic(args.port, args.address, args.baudrate)
    except KeyboardInterrupt:
        log("Отладка прервана пользователем", "WARNING")
    except Exception as e:
        log(f"Критическая ошибка: {e}", "ERROR")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
