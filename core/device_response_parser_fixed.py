#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер специфичного формата ответа Modbus RTU устройства (ИСПРАВЛЕННАЯ ВЕРСИЯ)
Разложение ответа по строкам с объяснениями полей
"""

def parse_specific_device_response(hex_response: str):
    """
    Парсит специфичный ответ устройства согласно спецификации пользователя

    Args:
        hex_response: Строка с hex данными ответа устройства

    Returns:
        dict: Распарсенные данные с объяснениями
    """

    # Удаляем пробелы и разбиваем на байты
    hex_bytes = hex_response.replace(' ', '').replace('\r', '').replace('\n', '')
    byte_list = [hex_bytes[i:i+2] for i in range(0, len(hex_bytes), 2)]

    if len(byte_list) < 32:
        return {"error": "Недостаточно данных для парсинга (минимум 32 байта)"}

    # Основные поля Modbus RTU ответа
    device_address = int(byte_list[0], 16)
    function_code = int(byte_list[1], 16)

    # Парсим специфичные поля устройства согласно спецификации
    parsed_data = {
        "modbus_header": {
            "device_address": f"{device_address} (0x{byte_list[0].upper()})",
            "function_code": f"{function_code} (0x{byte_list[1].upper()})"
        },
        "device_specific_data": {},
        "raw_hex": hex_response,
        "byte_count": len(byte_list)
    }

    try:
        # Magic (4 байта) - байты 4-7: 99 87 41 77 → 77418799 (обратный порядок)
        if len(byte_list) >= 8:
            magic_bytes = byte_list[4:8]  # байты 4-7 (индексы 4-7)
            magic_reversed = ''.join(reversed(magic_bytes))  # обратный порядок
            parsed_data["device_specific_data"]["magic"] = {
                "value": f"{int(magic_reversed, 16)} ({magic_reversed.upper()})",
                "hex_format": ' '.join(magic_bytes),
                "description": "Магическое число устройства",
                "bytes": f"Байты 4-7: {' '.join(magic_bytes)}",
                "reversed_hex": magic_reversed.upper()
            }

        # Software version (2 байта) - байты 8-9: 07 00 → V00.07
        if len(byte_list) >= 10:
            software_bytes = byte_list[8:10]  # байты 8-9 (индексы 8-9)
            sw_major = int(software_bytes[0], 16)
            sw_minor = int(software_bytes[1], 16)
            parsed_data["device_specific_data"]["software"] = {
                "value": f"V{sw_major:02d}.{sw_minor:02d}",
                "hex_format": ' '.join(software_bytes),
                "description": "Версия программного обеспечения",
                "bytes": f"Байты 8-9: {' '.join(software_bytes)}",
                "major": sw_major,
                "minor": sw_minor
            }

        # Hardware version (2 байта) - байты 10-11: 01 01 → V01.01
        if len(byte_list) >= 12:
            hardware_bytes = byte_list[10:12]  # байты 10-11 (индексы 10-11)
            hw_major = int(hardware_bytes[0], 16)
            hw_minor = int(hardware_bytes[1], 16)
            parsed_data["device_specific_data"]["hardware"] = {
                "value": f"V{hw_major:02d}.{hw_minor:02d}",
                "hex_format": ' '.join(hardware_bytes),
                "description": "Версия аппаратного обеспечения",
                "bytes": f"Байты 10-11: {' '.join(hardware_bytes)}",
                "major": hw_major,
                "minor": hw_minor
            }

        # VerStatus (4 байта) - байты 12-15: 0F 00 00 00
        if len(byte_list) >= 16:
            verstatus_bytes = byte_list[12:16]  # байты 12-15 (индексы 12-15)
            verstatus_value = int(''.join(verstatus_bytes), 16)
            parsed_data["device_specific_data"]["ver_status"] = {
                "value": f"0x{''.join(verstatus_bytes).upper()} ({verstatus_value})",
                "hex_format": ' '.join(verstatus_bytes),
                "description": "Статус версии",
                "bytes": f"Байты 12-15: {' '.join(verstatus_bytes)}",
                "decimal": verstatus_value
            }

        # Status (4 байта) - байты 16-19: 2F 48 50 4F → 4F50482F (обратный порядок)
        if len(byte_list) >= 20:
            status_bytes = byte_list[16:20]  # байты 16-19 (индексы 16-19)
            status_reversed = ''.join(reversed(status_bytes))  # обратный порядок
            # Пытаемся декодировать как ASCII
            try:
                status_text = bytes.fromhex(status_reversed).decode('ascii', errors='ignore').strip()
                if not status_text:
                    status_text = f"0x{status_reversed.upper()}"
            except:
                status_text = f"0x{status_reversed.upper()}"

            parsed_data["device_specific_data"]["status"] = {
                "value": status_text,
                "hex_format": ' '.join(status_bytes),
                "description": "Статус устройства",
                "bytes": f"Байты 16-19: {' '.join(status_bytes)}",
                "reversed_hex": status_reversed.upper()
            }

        # DI/DO/AI/AO (4 байта) - байты 20-23: 00 00 20 00 → 0/32/0/0
        if len(byte_list) >= 24:
            io_bytes = byte_list[20:24]  # байты 20-23 (индексы 20-23)
            di_count = int(io_bytes[0], 16)  # DI
            do_count = int(io_bytes[1], 16)  # DO
            ai_count = int(io_bytes[2], 16)  # AI
            ao_count = int(io_bytes[3], 16)  # AO

            parsed_data["device_specific_data"]["io_counts"] = {
                "value": f"{di_count}/{do_count}/{ai_count}/{ao_count}",
                "description": "DI/DO/AI/AO счетчики",
                "bytes": f"Байты 20-23: {' '.join(io_bytes)}",
                "digital_inputs": di_count,
                "digital_outputs": do_count,
                "analog_inputs": ai_count,
                "analog_outputs": ao_count
            }

        # ProductID (4 байта) - байты 28-31: FB 5F 19 63 → 63195FFB (обратный порядок)
        if len(byte_list) >= 32:
            product_bytes = byte_list[28:32]  # байты 28-31 (индексы 28-31)
            product_reversed = ''.join(reversed(product_bytes))  # обратный порядок
            parsed_data["device_specific_data"]["product_id"] = {
                "value": f"{int(product_reversed, 16)} ({product_reversed.upper()})",
                "hex_format": ' '.join(product_bytes),
                "description": "Идентификатор продукта",
                "bytes": f"Байты 28-31: {' '.join(product_bytes)}",
                "reversed_hex": product_reversed.upper()
            }

        # CRC (последние 2 байта, если есть)
        if len(byte_list) >= 34:
            crc_bytes = byte_list[-2:]  # последние 2 байта
            crc_value = int(''.join(crc_bytes), 16)
            parsed_data["crc"] = {
                "value": f"0x{''.join(crc_bytes).upper()} ({crc_value})",
                "hex_format": ' '.join(crc_bytes),
                "description": "Контрольная сумма CRC",
                "bytes": f"Последние байты: {' '.join(crc_bytes)}"
            }

    except Exception as e:
        parsed_data["parse_error"] = str(e)
        parsed_data["error"] = f"Ошибка парсинга: {str(e)}"

    return parsed_data

def print_parsed_response(parsed_data):
    """Красиво выводит распарсенные данные"""

    print("=" * 80)
    print("РАЗБОР ОТВЕТА УСТРОЙСТВА MODBUS RTU")
    print("=" * 80)

    # Заголовок Modbus
    print("\n[MODBUS_HEADER] ЗАГОЛОВОК MODBUS RTU:")
    print("-" * 40)
    for key, value in parsed_data["modbus_header"].items():
        print(f"  {key}: {value}")

    # Специфичные данные устройства
    if "device_specific_data" in parsed_data:
        print("\n[DEVICE_DATA] СПЕЦИФИЧНЫЕ ДАННЫЕ УСТРОЙСТВА:")
        print("-" * 40)

        for field_name, field_data in parsed_data["device_specific_data"].items():
            if isinstance(field_data, dict):
                print(f"\n  [FIELD] {field_data.get('description', field_name).upper()}:")
                print(f"      Значение: {field_data.get('value', 'N/A')}")
                if 'hex_format' in field_data:
                    print(f"      Hex: {field_data['hex_format']}")
                if 'bytes' in field_data:
                    print(f"      Позиция: {field_data['bytes']}")

                # Дополнительная информация для некоторых полей
                if "binary" in field_data:
                    print(f"      Binary: {field_data['binary']}")
                if "decimal" in field_data:
                    print(f"      Decimal: {field_data['decimal']}")
            else:
                print(f"\n  [FIELD] {field_name.upper()}: {field_data}")

    # CRC
    if "crc" in parsed_data:
        print("\n[CRC] КОНТРОЛЬНАЯ СУММА:")
        print("-" * 40)
        crc_data = parsed_data["crc"]
        print(f"  CRC: {crc_data['value']}")
        print(f"  Hex: {crc_data['hex_format']}")
        print(f"  Позиция: {crc_data['bytes']}")

    # Общая информация
    print(f"\n[INFO] ОБЩАЯ ИНФОРМАЦИЯ:")
    print("-" * 40)
    print(f"  Общая длина: {parsed_data['byte_count']} байт")
    print(f"  Hex данные: {parsed_data['raw_hex']}")

    print("\n" + "=" * 80)

def main():
    """Демонстрация парсинга конкретного ответа"""

    # Пример ответа от пользователя
    example_response = "0F 11 0F FF 99 87 41 77 07 00 01 01 0F 00 00 00 2F 48 50 4F 00 00 20 00 00 00 00 00 FB 5F 19 63 19 62 B1 B2 EB D7"

    print("ПРИМЕР ОТВЕТА УСТРОЙСТВА:")
    print(f"Исходные данные: {example_response}")
    print(f"Длина: {len(example_response.split())} байт")

    # Парсим ответ
    parsed = parse_specific_device_response(example_response)

    # Выводим результат
    print_parsed_response(parsed)

    # Показываем соответствие запрошенных полей
    print("\n[MAPPING] СООТВЕТСТВИЕ ЗАПРОШЕННЫХ ПОЛЕЙ:")
    print("-" * 50)

    if "device_specific_data" in parsed:
        fields_mapping = {
            "ProductID": "product_id",
            "Status": "status",
            "Magic": "magic",
            "Hardware": "hardware",
            "Software": "software",
            "DI": "digital_inputs",
            "DO": "digital_outputs",
            "AI": "analog_inputs",
            "AO": "analog_outputs"
        }

        for russian_name, english_key in fields_mapping.items():
            device_data = parsed.get("device_specific_data", {})
            if english_key in device_data:
                data = device_data[english_key]
                if isinstance(data, dict):
                    hex_format = data.get('hex_format', 'N/A')
                    value = data.get('value', 'N/A')
                    print(f"  {russian_name}: {hex_format} ({value})")
                else:
                    print(f"  {russian_name}: {data}")

if __name__ == "__main__":
    main()
