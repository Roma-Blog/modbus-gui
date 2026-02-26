#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест подключения к /dev/ttyUSB0
Параметры: адрес=4, скорость=38400
"""

import sys
import os
import serial
import time

# Добавляем путь к core модулям
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

PORT = "/dev/ttyUSB0"
ADDRESS = 4
BAUDRATE = 38400

def log(message: str, level: str = "INFO"):
    """Логирование с временными метками"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def test_serial_direct():
    """Тест 1: Прямое подключение через serial.Serial"""
    log("=" * 60)
    log(f"ТЕСТ 1: Прямое подключение к {PORT} @ {BAUDRATE}")
    log("=" * 60)
    
    try:
        ser = serial.Serial(
            port=PORT,
            baudrate=BAUDRATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.0
        )
        
        log(f"Порт открыт: is_open={ser.is_open}")
        
        if ser.is_open:
            log("[OK] Порт успешно открыт")
            ser.close()
            log("Порт закрыт")
            return True
        else:
            log("[FAIL] Порт не открыт")
            ser.close()
            return False
            
    except serial.SerialException as e:
        log(f"[FAIL] SerialException: {e}", "ERROR")
        return False
    except PermissionError as e:
        log(f"[FAIL] PermissionError: {e}", "ERROR")
        log("РЕШЕНИЕ: Добавьте пользователя в группу dialout:", "ERROR")
        log(f"  sudo usermod -aG dialout {os.environ.get('USER', 'user')}", "ERROR")
        log("  Затем выйдите из системы и зайдите снова", "ERROR")
        return False
    except Exception as e:
        log(f"[FAIL] Ошибка: {e}", "ERROR")
        return False

def test_modbus_connection():
    """Тест 2: Подключение через ModbusConnection"""
    log("=" * 60)
    log(f"ТЕСТ 2: ModbusConnection к {PORT} @ {BAUDRATE}")
    log("=" * 60)
    
    try:
        from core.modbus_connection import ModbusConnection
        
        connection = ModbusConnection(PORT, BAUDRATE)
        result = connection.connect()
        
        log(f"Результат: {result}")
        
        if result[0]:
            log("[OK] ModbusConnection: подключение успешно")
            connection.disconnect()
            return True
        else:
            log(f"[FAIL] ModbusConnection: {result[1]}")
            return False
            
    except Exception as e:
        log(f"[FAIL] Ошибка: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False

def test_modbus_client():
    """Тест 3: Подключение через ModbusRTUClient"""
    log("=" * 60)
    log(f"ТЕСТ 3: ModbusRTUClient к {PORT}, адрес={ADDRESS}, скорость={BAUDRATE}")
    log("=" * 60)
    
    try:
        from core.modbus_rtu_client import ModbusRTUClient
        
        client = ModbusRTUClient(PORT, ADDRESS, BAUDRATE)
        result = client.connect()
        
        log(f"Результат: {result}")
        
        if result[0]:
            log("[OK] ModbusRTUClient: подключение успешно")
            
            # Пробуем прочитать информацию об устройстве (команда 17)
            log("Чтение информации об устройстве (команда 17)...")
            device_info = client.get_device_info()
            
            if device_info:
                log("[OK] Устройство ответило:")
                for key, value in device_info.items():
                    log(f"  {key}: {value}")
            else:
                log("[WARN] Устройство не ответило на команду 17")
            
            client.disconnect()
            return True
        else:
            log(f"[FAIL] ModbusRTUClient: {result[1]}")
            return False
            
    except Exception as e:
        log(f"[FAIL] Ошибка: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False

def main():
    log("=" * 60)
    log(f"ТЕСТ ПОДКЛЮЧЕНИЯ К {PORT}")
    log(f"Параметры: адрес={ADDRESS}, скорость={BAUDRATE}")
    log("=" * 60)
    
    results = {}
    
    # Тест 1: Raw serial
    results["serial_direct"] = test_serial_direct()
    time.sleep(0.5)
    
    # Тест 2: ModbusConnection
    results["modbus_connection"] = test_modbus_connection()
    time.sleep(0.5)
    
    # Тест 3: ModbusRTUClient
    results["modbus_client"] = test_modbus_client()
    
    # Итоги
    log("=" * 60)
    log("ИТОГИ:")
    for test_name, result in results.items():
        status = "[OK]" if result else "[FAIL]"
        log(f"  {test_name}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    log(f"\nПройдено: {passed}/{total} тестов")
    
    if passed == total:
        log("[SUCCESS] ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
    else:
        log("[FAIL] ЕСТЬ ПРОБЛЕМЫ С ПОДКЛЮЧЕНИЕМ")
        log("\nВОЗМОЖНАЯ ПРИЧИНА: нет прав доступа к порту")
        log(f"РЕШЕНИЕ: sudo usermod -aG dialout {os.environ.get('USER', 'user')}")
        log("Затем выйдите из системы и зайдите снова (или перезагрузитесь)")

if __name__ == "__main__":
    main()
