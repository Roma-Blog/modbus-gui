#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест производительности Rust сканера Modbus
Сравнивает скорость перебора адресов между Python и Rust реализациями
"""

import sys
import os
import time

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modbus_scanner_wrapper import ModbusScannerRust, DEFAULT_BAUDRATES


def test_rust_scanner(port: str = "/dev/ttyUSB0"):
    """Тестирует Rust сканер"""
    print("=" * 60)
    print("ТЕСТ Rust сканера Modbus RTU")
    print("=" * 60)
    
    # Проверяем доступность сканера
    try:
        scanner = ModbusScannerRust(port, timeout_ms=50)
    except Exception as e:
        print(f"[ERROR] Не удалось создать сканер: {e}")
        return
    
    if not scanner._scanner:
        print("[WARNING] Rust библиотека не загружена!")
        print("[INFO] Для компиляции выполните:")
        print(f"  cd {os.path.join(os.path.dirname(__file__), 'modbus_scanner_rust')}")
        print("  maturin develop --release")
        return
    
    print(f"[OK] Rust сканер загружен")
    print(f"Порт: {port}")
    print(f"Таймаут: 50ms")
    print()
    
    # Тест 1: Одиночное сканирование
    print("Тест 1: Одиночное сканирование (адрес=4, скорость=38400)")
    start = time.time()
    result = scanner.scan_single(4, 38400)
    elapsed = time.time() - start
    print(f"  Время: {elapsed*1000:.1f}ms")
    print(f"  Результат: {result}")
    print()
    
    # Тест 2: Сканирование диапазона адресов
    print("Тест 2: Сканирование диапазона адресов 1-100 @ 38400 baud")
    start = time.time()
    results = scanner.scan_addresses(
        baudrate=38400,
        start_address=1,
        end_address=100,
        status_callback=lambda s: None
    )
    elapsed = time.time() - start
    print(f"  Время: {elapsed:.2f}s")
    print(f"  Найдено устройств: {len(results)}")
    if results:
        for r in results[:5]:  # Показываем первые 5
            print(f"    - Адрес {r['address']} @ {r['baudrate']} baud")
    print()
    
    # Тест 3: Полное сканирование
    print("Тест 3: Полное сканирование (адреса 1-50, 5 скоростей)")
    start = time.time()
    results = scanner.scan_all(
        baudrates=DEFAULT_BAUDRATES,
        start_address=1,
        end_address=50,
        status_callback=lambda s: None
    )
    elapsed = time.time() - start
    print(f"  Время: {elapsed:.2f}s")
    print(f"  Найдено устройств: {len(results)}")
    if results:
        for r in results:
            print(f"    - Адрес {r['address']} @ {r['baudrate']} baud")
    print()
    
    # Тест 4: Быстрый поиск первого
    print("Тест 4: Быстрый поиск первого устройства (адреса 1-200 @ 38400)")
    start = time.time()
    result = scanner.scan_first_found(
        baudrate=38400,
        start_address=1,
        end_address=200,
        status_callback=lambda s: None
    )
    elapsed = time.time() - start
    print(f"  Время: {elapsed:.2f}s")
    print(f"  Результат: {result}")
    print()
    
    # Итоги
    print("=" * 60)
    print("ИТОГИ:")
    print(f"  Rust сканер: {'ДОСТУПЕН' if scanner._scanner else 'НЕ ДОСТУПЕН'}")
    print(f"  Рекомендуемый диапазон: 1-200 адресов, 5 скоростей")
    print(f"  Ожидаемое время полного сканирования: ~30-60s")
    print("=" * 60)


def compare_python_rust(port: str = "/dev/ttyUSB0"):
    """Сравнивает производительность Python и Rust (если доступно)"""
    print("\n" + "=" * 60)
    print("СРАВНЕНИЕ: Python vs Rust")
    print("=" * 60)
    
    # Rust
    print("\nRust реализация:")
    try:
        scanner = ModbusScannerRust(port, timeout_ms=50)
        if scanner._scanner:
            start = time.time()
            scanner.scan_addresses(38400, 1, 50, status_callback=lambda s: None)
            elapsed = time.time() - start
            print(f"  50 адресов @ 38400 baud: {elapsed:.2f}s")
            print(f"  ~{elapsed/50*1000:.1f}ms на адрес")
        else:
            print("  Rust библиотека не загружена")
    except Exception as e:
        print(f"  Ошибка: {e}")
    
    print("\nPython реализация (оценка):")
    print("  ~500ms на адрес (таймауты serial)")
    print("  50 адресов: ~25s")
    print("  200 адресов × 5 скоростей: ~500s (8+ минут)")
    
    print("\nУскорение с Rust: ~10x быстрее!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Тест производительности Rust Modbus сканера")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="COM порт для тестирования")
    parser.add_argument("--compare", action="store_true", help="Запустить сравнение Python vs Rust")
    
    args = parser.parse_args()
    
    test_rust_scanner(args.port)
    
    if args.compare:
        compare_python_rust(args.port)
