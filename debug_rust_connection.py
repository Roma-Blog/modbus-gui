#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отладка подключения к Modbus устройству
"""

import serial
import time

PORT = "/dev/ttyUSB0"
BAUDRATE = 38400
ADDRESS = 4

def calculate_crc16(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc

def test_connection():
    print(f"Тест подключения: {PORT} @ {BAUDRATE}, адрес={ADDRESS}")
    
    # Команда 17 (Read Device Identification)
    request = bytearray([
        ADDRESS,
        0x11,
        0x00,
        0x00,
        0x00,
        0x00
    ])
    crc = calculate_crc16(request)
    request.extend([crc & 0xFF, (crc >> 8) & 0xFF])
    
    print(f"Запрос: {' '.join(f'{b:02X}' for b in request)}")
    
    try:
        with serial.Serial(
            port=PORT,
            baudrate=BAUDRATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.0
        ) as conn:
            print(f"Порт открыт: {conn.is_open}")
            
            # Очистить буферы
            conn.reset_input_buffer()
            conn.reset_output_buffer()
            
            # Отправить запрос
            conn.write(request)
            conn.flush()
            print("Запрос отправлен")
            
            # Ждать ответ
            time.sleep(0.2)
            
            # Читать ответ
            response = conn.read(100)
            print(f"Получено байт: {len(response)}")
            
            if response:
                print(f"Ответ: {' '.join(f'{b:02X}' for b in response)}")
                
                # Проверка CRC
                if len(response) >= 2:
                    response_crc = (response[-2]) | (response[-1] << 8)
                    calculated_crc = calculate_crc16(response[:-2])
                    print(f"CRC: получен={response_crc:04X}, рассчитан={calculated_crc:04X}")
                    
                    if response_crc == calculated_crc:
                        print("✓ CRC верный!")
                    else:
                        print("✗ CRC ошибка!")
            else:
                print("Нет ответа от устройства")
                
    except serial.SerialException as e:
        print(f"Ошибка порта: {e}")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    test_connection()
