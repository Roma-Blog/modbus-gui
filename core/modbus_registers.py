#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modbus Registers Module
Модуль для работы с регистрами Modbus
"""

import time
import logging
from typing import Optional, List, Union
import serial

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    force=True)
logger = logging.getLogger(__name__)

class ModbusRegisters:
    """Класс для работы с регистрами Modbus"""

    def __init__(self, connection: serial.Serial, device_address: int):
        """
        Инициализация

        Args:
            connection: Активное соединение
            device_address: Адрес Modbus устройства (1-247)
        """
        self.connection = connection
        self.device_address = device_address

    def read_holding_registers(self, start_address: int, count: int) -> Optional[list]:
        """
        Читает holding регистры (функция 3)

        Args:
            start_address: Начальный адрес регистра
            count: Количество регистров для чтения

        Returns:
            list или None: Список значений регистров
        """
        print(f"[DEBUG] Начинаем чтение holding регистров: адрес={start_address}, количество={count}")
        logger.info(f"Чтение holding регистров: start_address={start_address}, count={count}")

        result = self._read_registers_with_function(start_address, count, 0x03, "Holding Registers")
        if result:
            return result

        print(f"[INFO] Holding registers не отвечают, пробуем Input Registers...")
        return self._read_registers_with_function(start_address, count, 0x04, "Input Registers")

    def _read_registers_with_function(self, start_address: int, count: int, function_code: int, register_type: str) -> Optional[list]:
        """
        Читает регистры с указанной функцией Modbus

        Args:
            start_address: Начальный адрес регистра
            count: Количество регистров для чтения
            function_code: Код функции Modbus (3 или 4)
            register_type: Тип регистров для отладки

        Returns:
            list или None: Список значений регистров
        """
        try:
            if not self.connection or not self.connection.is_open:
                print("[ERROR] Соединение не установлено или порт закрыт")
                logger.error("Соединение не установлено при попытке чтения регистров")
                return None

            request = bytearray([
                self.device_address,
                function_code,
                (start_address >> 8) & 0xFF,
                start_address & 0xFF,
                (count >> 8) & 0xFF,
                count & 0xFF
            ])

            crc = self._calculate_crc16(request)
            request.extend([crc & 0xFF, (crc >> 8) & 0xFF])

            request_hex = " ".join([f"{b:02X}" for b in request])
            print(f"[DEBUG] Отправляемый запрос ({register_type}): {request_hex}")
            logger.debug(f"Отправляемый запрос ({register_type}): {request_hex}")

            self.connection.write(request)
            self.connection.flush()

            print(f"[DEBUG] Ждем ответ от устройства ({register_type})...")
            time.sleep(0.2)

            try:
                response = self.connection.read(100)
            except OSError as e:
                print(f"[ERROR] Ошибка чтения из порта при чтении {register_type.lower()}: {e}")
                logger.error(f"Ошибка чтения из порта при чтении {register_type.lower()}: {e}")
                return None

            if response:
                response_hex = " ".join([f"{b:02X}" for b in response])
                print(f"[DEBUG] Полученный ответ ({register_type}): {response_hex} (длина: {len(response)} байт)")
                logger.debug(f"Полученный ответ ({register_type}): {response_hex}")
            else:
                print(f"[ERROR] Нет ответа от устройства ({register_type})")
                logger.error(f"Нет ответа от устройства при чтении {register_type}")
                return None

            if len(response) < 5:
                print(f"[ERROR] Ответ слишком короткий ({register_type}): {len(response)} байт (минимум 5)")
                logger.error(f"Ответ слишком короткий ({register_type}): {len(response)} байт")
                return None

            response_crc = (response[-2]) | (response[-1] << 8)
            calculated_crc = self._calculate_crc16(response[:-2])

            print(f"[DEBUG] CRC ({register_type}): получен={response_crc:04X}, рассчитан={calculated_crc:04X}")

            if response_crc != calculated_crc:
                print(f"[ERROR] Неверный CRC в ответе ({register_type})")
                logger.error(f"Неверный CRC в ответе ({register_type})")
                print(f"[INFO] Возвращаем пустой список вместо None для безопасности")
                return []

            if response[0] != self.device_address:
                print(f"[ERROR] Неверный адрес устройства в ответе ({register_type}): получен={response[0]}, ожидался={self.device_address}")
                logger.error(f"Неверный адрес устройства в ответе ({register_type}): {response[0]} != {self.device_address}")
                return None

            if response[1] != function_code:
                if response[1] == 0x11:
                    print(f"[INFO] Устройство ответило function 11 на запросы holding registers, извлекаем регистры из ответа")
                    logger.info(f"Устройство ответило function 11 на запрос {register_type}")

                    registers = []
                    hex_parts = [f"{b:02X}" for b in response]

                    for i in range(8, len(hex_parts), 2):
                        if i + 1 < len(hex_parts):
                            try:
                                reg_value = int(hex_parts[i], 16) << 8 | int(hex_parts[i+1], 16)
                                registers.append(reg_value)
                                if len(registers) >= count:
                                    break
                            except ValueError:
                                continue

                    if registers:
                        print(f"[SUCCESS] Извлечено {len(registers)} регистров из ответа function 11: {registers}")
                        logger.info(f"Извлечено {len(registers)} регистров из ответа function 11")
                        return registers
                    else:
                        print(f"[ERROR] Не удалось извлечь регистры из ответа function 11")
                        logger.error("Не удалось извлечь регистры из ответа function 11")
                        return None
                else:
                    print(f"[ERROR] Неверная функция в ответе ({register_type}): получена={response[1]:02X}, ожидалась={function_code:02X}")
                    logger.error(f"Неверная функция в ответе ({register_type}): {response[1]:02X} != {function_code:02X}")
                    return None

            byte_count = response[2]
            expected_length = 5 + byte_count

            print(f"[DEBUG] Байтов данных ({register_type}): {byte_count}, ожидаемая длина ответа: {expected_length}")

            if len(response) < expected_length:
                print(f"[ERROR] Ответ короче ожидаемого ({register_type}): {len(response)} < {expected_length}")
                logger.error(f"Ответ короче ожидаемого ({register_type}): {len(response)} < {expected_length}")
                return None

            registers = []
            for i in range(0, byte_count, 2):
                if 3 + i + 1 < len(response):
                    value = (response[3 + i] << 8) | response[3 + i + 1]
                    registers.append(value)
                    print(f"[DEBUG] Регистр {start_address + i//2} ({register_type}): {value} (0x{value:04X})")

            print(f"[SUCCESS] Успешно прочитано {len(registers)} {register_type.lower()}: {registers}")
            logger.info(f"Успешно прочитано {len(registers)} {register_type.lower()}")
            return registers

        except Exception as e:
            print(f"[ERROR] Исключение при чтении {register_type.lower()}: {e}")
            logger.error(f"Исключение при чтении {register_type.lower()}: {e}")
            return None

    def write_holding_registers(self, start_address: int, values: List[int]) -> bool:
        """
        Записывает holding регистры (функция 16 - Preset Multiple Registers)

        Args:
            start_address: Начальный адрес регистра
            values: Список значений для записи

        Returns:
            bool: True если запись успешна, False иначе
        """
        print(f"[WRITE_DEBUG] Начинаем запись регистров: адрес={start_address}, значения={values}")

        try:
            if not self.connection:
                print("[WRITE_ERROR] Соединение не инициализировано (connection is None)")
                logger.error("Соединение не инициализировано при попытке записи регистров")
                return False

            if not hasattr(self.connection, 'is_open') or not self.connection.is_open:
                print("[WRITE_ERROR] Порт не открыт или недоступен")
                logger.error("Порт не открыт при попытке записи регистров")
                return False

            print(f"[WRITE_DEBUG] Соединение активно, порт: {self.connection.port}")

            if not values or len(values) == 0:
                print("[WRITE_ERROR] Нет значений для записи")
                logger.error("Нет значений для записи в регистры")
                return False

            count = len(values)
            byte_count = count * 2

            print(f"[WRITE_DEBUG] Количество регистров: {count}, байтов данных: {byte_count}")

            request = bytearray([
                self.device_address,
                0x10,
                (start_address >> 8) & 0xFF,
                start_address & 0xFF,
                (count >> 8) & 0xFF,
                count & 0xFF,
                byte_count
            ])

            for value in values:
                request.extend([(value >> 8) & 0xFF, value & 0xFF])

            crc = self._calculate_crc16(request)
            request.extend([crc & 0xFF, (crc >> 8) & 0xFF])

            request_hex = " ".join([f"{b:02X}" for b in request])
            print(f"[WRITE_DEBUG] Отправляемый запрос записи регистров: {request_hex}")
            print(f"[WRITE_DEBUG] Адрес устройства: {self.device_address}, Функция: 0x10, CRC: {crc:04X}")
            logger.debug(f"Отправляемый запрос записи регистров: {request_hex}")

            print(f"[WRITE_DEBUG] Отправляем запрос...")
            bytes_written = self.connection.write(request)
            self.connection.flush()
            print(f"[WRITE_DEBUG] Записано байтов: {bytes_written}")

            print(f"[WRITE_DEBUG] Ждем ответ от устройства на запись регистров...")
            time.sleep(0.5)

            try:
                response = self.connection.read(100)
                print(f"[WRITE_DEBUG] Прочитано байтов из порта: {len(response) if response else 0}")
            except OSError as e:
                print(f"[WRITE_ERROR] Ошибка чтения из порта: {e}")
                logger.error(f"Ошибка чтения из порта при записи регистров: {e}")
                return False

            if response:
                response_hex = " ".join([f"{b:02X}" for b in response])
                print(f"[WRITE_DEBUG] Полученный ответ на запись: {response_hex} (длина: {len(response)} байт)")
                logger.debug(f"Полученный ответ на запись: {response_hex}")
            else:
                print(f"[WRITE_ERROR] Нет ответа от устройства на запись регистров")
                logger.error("Нет ответа от устройства на запись регистров")
                return False

            if len(response) < 8:
                print(f"[WRITE_ERROR] Ответ слишком короткий: {len(response)} байт (минимум 8)")
                logger.error(f"Ответ слишком короткий: {len(response)} байт")
                return False

            response_crc = (response[-2]) | (response[-1] << 8)
            calculated_crc = self._calculate_crc16(response[:-2])

            print(f"[WRITE_DEBUG] CRC записи: получен={response_crc:04X}, рассчитан={calculated_crc:04X}")

            if response_crc != calculated_crc:
                print(f"[WRITE_ERROR] Неверный CRC в ответе на запись")
                logger.error("Неверный CRC в ответе на запись регистров")
                return False

            if response[0] != self.device_address:
                print(f"[WRITE_ERROR] Неверный адрес устройства в ответе: получен={response[0]}, ожидался={self.device_address}")
                logger.error(f"Неверный адрес устройства в ответе: {response[0]} != {self.device_address}")
                return False

            if response[1] != 0x10:
                if response[1] & 0x80:
                    exception_code = response[2]
                    print(f"[WRITE_ERROR] Код исключения Modbus: {exception_code}")
                    print(f"[WRITE_DEBUG] Расшифровка кода исключения:")
                    if exception_code == 1:
                        print("  1 - Illegal Function - Функция не поддерживается")
                    elif exception_code == 2:
                        print("  2 - Illegal Data Address - Неверный адрес данных")
                    elif exception_code == 3:
                        print("  3 - Illegal Data Value - Неверное значение данных")
                    elif exception_code == 4:
                        print("  4 - Slave Device Failure - Сбой устройства")
                    elif exception_code == 5:
                        print("  5 - Acknowledge - Подтверждение (длительная операция)")
                    elif exception_code == 6:
                        print("  6 - Slave Device Busy - Устройство занято")
                    else:
                        print(f"  {exception_code} - Неизвестный код исключения")
                    logger.error(f"Код исключения Modbus: {exception_code}")
                    return False
                else:
                    print(f"[WRITE_ERROR] Неверная функция в ответе: получена={response[1]:02X}, ожидалась=10")
                    logger.error(f"Неверная функция в ответе: {response[1]:02X} != 10")
                    return False

            response_start = (response[2] << 8) | response[3]
            response_count = (response[4] << 8) | response[5]

            print(f"[WRITE_DEBUG] Проверка ответа: адрес {response_start} (ожидался {start_address}), количество {response_count} (ожидалось {count})")

            if response_start != start_address or response_count != count:
                print(f"[WRITE_WARNING] Несоответствие в ответе: адрес {response_start} != {start_address}, количество {response_count} != {count}")
                logger.warning(f"Несоответствие в ответе: адрес {response_start} != {start_address}, количество {response_count} != {count}")

            print(f"[WRITE_SUCCESS] Успешно записано {count} holding регистров начиная с адреса {start_address}")
            logger.info(f"Успешно записано {count} holding регистров начиная с адреса {start_address}")
            return True

        except Exception as e:
            print(f"[WRITE_ERROR] Исключение при записи регистров: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Исключение при записи регистров: {e}")
            return False

    def write_single_register(self, address: int, value: int) -> bool:
        """
        Записывает один holding регистр (функция 6 - Preset Single Register)

        Args:
            address: Адрес регистра
            value: Значение для записи

        Returns:
            bool: True если запись успешна, False иначе
        """
        print(f"[WRITE_SINGLE_DEBUG] Начинаем запись одного регистра: адрес={address}, значение={value}")

        try:
            if not self.connection:
                print("[WRITE_SINGLE_ERROR] Соединение не инициализировано (connection is None)")
                logger.error("Соединение не инициализировано при попытке записи одного регистра")
                return False

            if not hasattr(self.connection, 'is_open') or not self.connection.is_open:
                print("[WRITE_SINGLE_ERROR] Порт не открыт или недоступен")
                logger.error("Порт не открыт при попытке записи одного регистра")
                return False

            print(f"[WRITE_SINGLE_DEBUG] Соединение активно, порт: {self.connection.port}")

            request = bytearray([
                self.device_address,
                0x06,
                (address >> 8) & 0xFF,
                address & 0xFF,
                (value >> 8) & 0xFF,
                value & 0xFF
            ])

            crc = self._calculate_crc16(request)
            request.extend([crc & 0xFF, (crc >> 8) & 0xFF])

            request_hex = " ".join([f"{b:02X}" for b in request])
            print(f"[WRITE_SINGLE_DEBUG] Отправляемый запрос записи одного регистра: {request_hex}")
            print(f"[WRITE_SINGLE_DEBUG] Адрес устройства: {self.device_address}, Функция: 0x06, CRC: {crc:04X}")
            logger.debug(f"Отправляемый запрос записи одного регистра: {request_hex}")

            print(f"[WRITE_SINGLE_DEBUG] Отправляем запрос...")
            bytes_written = self.connection.write(request)
            self.connection.flush()
            print(f"[WRITE_SINGLE_DEBUG] Записано байтов: {bytes_written}")

            print(f"[WRITE_SINGLE_DEBUG] Ждем ответ от устройства на запись одного регистра...")
            time.sleep(0.3)

            try:
                response = self.connection.read(100)
                print(f"[WRITE_SINGLE_DEBUG] Прочитано байтов из порта: {len(response) if response else 0}")
            except OSError as e:
                print(f"[WRITE_SINGLE_ERROR] Ошибка чтения из порта: {e}")
                logger.error(f"Ошибка чтения из порта при записи одного регистра: {e}")
                return False

            if response:
                response_hex = " ".join([f"{b:02X}" for b in response])
                print(f"[WRITE_SINGLE_DEBUG] Полученный ответ на запись одного регистра: {response_hex} (длина: {len(response)} байт)")
                logger.debug(f"Полученный ответ на запись одного регистра: {response_hex}")
            else:
                print(f"[WRITE_SINGLE_ERROR] Нет ответа от устройства на запись одного регистра")
                logger.error("Нет ответа от устройства на запись одного регистра")
                return False

            if len(response) < 8:
                print(f"[WRITE_SINGLE_ERROR] Ответ слишком короткий: {len(response)} байт (минимум 8)")
                logger.error(f"Ответ слишком короткий: {len(response)} байт")
                return False

            response_crc = (response[-2]) | (response[-1] << 8)
            calculated_crc = self._calculate_crc16(response[:-2])

            print(f"[WRITE_SINGLE_DEBUG] CRC записи одного регистра: получен={response_crc:04X}, рассчитан={calculated_crc:04X}")

            if response_crc != calculated_crc:
                print(f"[WRITE_SINGLE_ERROR] Неверный CRC в ответе на запись одного регистра")
                logger.error("Неверный CRC в ответе на запись одного регистра")
                return False

            if response[0] != self.device_address:
                print(f"[WRITE_SINGLE_ERROR] Неверный адрес устройства в ответе: получен={response[0]}, ожидался={self.device_address}")
                logger.error(f"Неверный адрес устройства в ответе: {response[0]} != {self.device_address}")
                return False

            if response[1] != 0x06:
                if response[1] & 0x80:
                    exception_code = response[2]
                    print(f"[WRITE_SINGLE_ERROR] Код исключения Modbus: {exception_code}")
                    print(f"[WRITE_SINGLE_DEBUG] Расшифровка кода исключения:")
                    if exception_code == 1:
                        print("  1 - Illegal Function - Функция не поддерживается")
                    elif exception_code == 2:
                        print("  2 - Illegal Data Address - Неверный адрес данных")
                    elif exception_code == 3:
                        print("  3 - Illegal Data Value - Неверное значение данных")
                    elif exception_code == 4:
                        print("  4 - Slave Device Failure - Сбой устройства")
                    elif exception_code == 5:
                        print("  5 - Acknowledge - Подтверждение (длительная операция)")
                    elif exception_code == 6:
                        print("  6 - Slave Device Busy - Устройство занято")
                    else:
                        print(f"  {exception_code} - Неизвестный код исключения")
                    logger.error(f"Код исключения Modbus: {exception_code}")
                    return False
                else:
                    print(f"[WRITE_SINGLE_ERROR] Неверная функция в ответе: получена={response[1]:02X}, ожидалась=06")
                    logger.error(f"Неверная функция в ответе: {response[1]:02X} != 06")
                    return False

            response_address = (response[2] << 8) | response[3]
            response_value = (response[4] << 8) | response[5]

            print(f"[WRITE_SINGLE_DEBUG] Проверка ответа: адрес {response_address} (ожидался {address}), значение {response_value} (ожидалось {value})")

            if response_address != address or response_value != value:
                print(f"[WRITE_SINGLE_WARNING] Несоответствие в ответе: адрес {response_address} != {address}, значение {response_value} != {value}")
                logger.warning(f"Несоответствие в ответе: адрес {response_address} != {address}, значение {response_value} != {value}")

            print(f"[WRITE_SINGLE_SUCCESS] Успешно записан holding регистр по адресу {address}: {value}")
            logger.info(f"Успешно записан holding регистр по адресу {address}: {value}")
            return True

        except Exception as e:
            print(f"[WRITE_SINGLE_ERROR] Исключение при записи одного регистра: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Исключение при записи одного регистра: {e}")
            return False

    def write_single_coil(self, address: int, value: bool) -> bool:
        """
        Записывает один coil (функция 5 - Force Single Coil)

        Args:
            address: Адрес coil
            value: Значение для записи (True/False)

        Returns:
            bool: True если запись успешна, False иначе
        """
        print(f"[WRITE_COIL_DEBUG] Начинаем запись одного coil: адрес={address}, значение={value}")

        try:
            if not self.connection:
                print("[WRITE_COIL_ERROR] Соединение не инициализировано (connection is None)")
                logger.error("Соединение не инициализировано при попытке записи одного coil")
                return False

            if not hasattr(self.connection, 'is_open') or not self.connection.is_open:
                print("[WRITE_COIL_ERROR] Порт не открыт или недоступен")
                logger.error("Порт не открыт при попытке записи одного coil")
                return False

            print(f"[WRITE_COIL_DEBUG] Соединение активно, порт: {self.connection.port}")

            # Для Modbus: FF00 = True (ON), 0000 = False (OFF)
            coil_value = 0xFF00 if value else 0x0000

            request = bytearray([
                self.device_address,
                0x05,
                (address >> 8) & 0xFF,
                address & 0xFF,
                (coil_value >> 8) & 0xFF,
                coil_value & 0xFF
            ])

            crc = self._calculate_crc16(request)
            request.extend([crc & 0xFF, (crc >> 8) & 0xFF])

            request_hex = " ".join([f"{b:02X}" for b in request])
            print(f"[WRITE_COIL_DEBUG] Отправляемый запрос записи одного coil: {request_hex}")
            print(f"[WRITE_COIL_DEBUG] Адрес устройства: {self.device_address}, Функция: 0x05, CRC: {crc:04X}")
            logger.debug(f"Отправляемый запрос записи одного coil: {request_hex}")

            print(f"[WRITE_COIL_DEBUG] Отправляем запрос...")
            bytes_written = self.connection.write(request)
            self.connection.flush()
            print(f"[WRITE_COIL_DEBUG] Записано байтов: {bytes_written}")

            print(f"[WRITE_COIL_DEBUG] Ждем ответ от устройства на запись одного coil...")
            time.sleep(0.3)

            try:
                response = self.connection.read(100)
                print(f"[WRITE_COIL_DEBUG] Прочитано байтов из порта: {len(response) if response else 0}")
            except OSError as e:
                print(f"[WRITE_COIL_ERROR] Ошибка чтения из порта: {e}")
                logger.error(f"Ошибка чтения из порта при записи одного coil: {e}")
                return False

            if response:
                response_hex = " ".join([f"{b:02X}" for b in response])
                print(f"[WRITE_COIL_DEBUG] Полученный ответ на запись одного coil: {response_hex} (длина: {len(response)} байт)")
                logger.debug(f"Полученный ответ на запись одного coil: {response_hex}")
            else:
                print(f"[WRITE_COIL_ERROR] Нет ответа от устройства на запись одного coil")
                logger.error("Нет ответа от устройства на запись одного coil")
                return False

            if len(response) < 8:
                print(f"[WRITE_COIL_ERROR] Ответ слишком короткий: {len(response)} байт (минимум 8)")
                logger.error(f"Ответ слишком короткий: {len(response)} байт")
                return False

            response_crc = (response[-2]) | (response[-1] << 8)
            calculated_crc = self._calculate_crc16(response[:-2])

            print(f"[WRITE_COIL_DEBUG] CRC записи одного coil: получен={response_crc:04X}, рассчитан={calculated_crc:04X}")

            if response_crc != calculated_crc:
                print(f"[WRITE_COIL_ERROR] Неверный CRC в ответе на запись одного coil")
                logger.error("Неверный CRC в ответе на запись одного coil")
                return False

            if response[0] != self.device_address:
                print(f"[WRITE_COIL_ERROR] Неверный адрес устройства в ответе: получен={response[0]}, ожидался={self.device_address}")
                logger.error(f"Неверный адрес устройства в ответе: {response[0]} != {self.device_address}")
                return False

            if response[1] != 0x05:
                if response[1] & 0x80:
                    exception_code = response[2]
                    print(f"[WRITE_COIL_ERROR] Код исключения Modbus: {exception_code}")
                    print(f"[WRITE_COIL_DEBUG] Расшифровка кода исключения:")
                    if exception_code == 1:
                        print("  1 - Illegal Function - Функция не поддерживается")
                    elif exception_code == 2:
                        print("  2 - Illegal Data Address - Неверный адрес данных")
                    elif exception_code == 3:
                        print("  3 - Illegal Data Value - Неверное значение данных")
                    elif exception_code == 4:
                        print("  4 - Slave Device Failure - Сбой устройства")
                    elif exception_code == 5:
                        print("  5 - Acknowledge - Подтверждение (длительная операция)")
                    elif exception_code == 6:
                        print("  6 - Slave Device Busy - Устройство занято")
                    else:
                        print(f"  {exception_code} - Неизвестный код исключения")
                    logger.error(f"Код исключения Modbus: {exception_code}")
                    return False
                else:
                    print(f"[WRITE_COIL_ERROR] Неверная функция в ответе: получена={response[1]:02X}, ожидалась=05")
                    logger.error(f"Неверная функция в ответе: {response[1]:02X} != 05")
                    return False

            response_address = (response[2] << 8) | response[3]
            response_value = (response[4] << 8) | response[5]

            print(f"[WRITE_COIL_DEBUG] Проверка ответа: адрес {response_address} (ожидался {address}), значение {response_value} (ожидалось {coil_value})")

            if response_address != address or response_value != coil_value:
                print(f"[WRITE_COIL_WARNING] Несоответствие в ответе: адрес {response_address} != {address}, значение {response_value} != {coil_value}")
                logger.warning(f"Несоответствие в ответе: адрес {response_address} != {address}, значение {response_value} != {coil_value}")

            print(f"[WRITE_COIL_SUCCESS] Успешно записан coil по адресу {address}: {value}")
            logger.info(f"Успешно записан coil по адресу {address}: {value}")
            return True

        except Exception as e:
            print(f"[WRITE_COIL_ERROR] Исключение при записи одного coil: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Исключение при записи одного coil: {e}")
            return False

    def write_multiple_coils(self, start_address: int, values: List[bool]) -> bool:
        """
        Записывает несколько coils (функция 15 - Force Multiple Coils)

        Args:
            start_address: Начальный адрес coil
            values: Список значений для записи (True/False)

        Returns:
            bool: True если запись успешна, False иначе
        """
        print(f"[WRITE_COILS_DEBUG] Начинаем запись coils: адрес={start_address}, значения={values}")

        try:
            if not self.connection:
                print("[WRITE_COILS_ERROR] Соединение не инициализировано (connection is None)")
                logger.error("Соединение не инициализировано при попытке записи coils")
                return False

            if not hasattr(self.connection, 'is_open') or not self.connection.is_open:
                print("[WRITE_COILS_ERROR] Порт не открыт или недоступен")
                logger.error("Порт не открыт при попытке записи coils")
                return False

            print(f"[WRITE_COILS_DEBUG] Соединение активно, порт: {self.connection.port}")

            if not values or len(values) == 0:
                print("[WRITE_COILS_ERROR] Нет значений для записи")
                logger.error("Нет значений для записи в coils")
                return False

            count = len(values)
            byte_count = (count + 7) // 8  # Количество байтов для coils

            print(f"[WRITE_COILS_DEBUG] Количество coils: {count}, байтов данных: {byte_count}")

            request = bytearray([
                self.device_address,
                0x0F,
                (start_address >> 8) & 0xFF,
                start_address & 0xFF,
                (count >> 8) & 0xFF,
                count & 0xFF,
                byte_count
            ])

            # Преобразуем список bool в байты
            coil_bytes = bytearray(byte_count)
            for i, value in enumerate(values):
                if value:
                    byte_index = i // 8
                    bit_index = i % 8
                    coil_bytes[byte_index] |= (1 << bit_index)

            request.extend(coil_bytes)

            crc = self._calculate_crc16(request)
            request.extend([crc & 0xFF, (crc >> 8) & 0xFF])

            request_hex = " ".join([f"{b:02X}" for b in request])
            print(f"[WRITE_COILS_DEBUG] Отправляемый запрос записи coils: {request_hex}")
            print(f"[WRITE_COILS_DEBUG] Адрес устройства: {self.device_address}, Функция: 0x0F, CRC: {crc:04X}")
            logger.debug(f"Отправляемый запрос записи coils: {request_hex}")

            print(f"[WRITE_COILS_DEBUG] Отправляем запрос...")
            bytes_written = self.connection.write(request)
            self.connection.flush()
            print(f"[WRITE_COILS_DEBUG] Записано байтов: {bytes_written}")

            print(f"[WRITE_COILS_DEBUG] Ждем ответ от устройства на запись coils...")
            time.sleep(0.5)

            try:
                response = self.connection.read(100)
                print(f"[WRITE_COILS_DEBUG] Прочитано байтов из порта: {len(response) if response else 0}")
            except OSError as e:
                print(f"[WRITE_COILS_ERROR] Ошибка чтения из порта: {e}")
                logger.error(f"Ошибка чтения из порта при записи coils: {e}")
                return False

            if response:
                response_hex = " ".join([f"{b:02X}" for b in response])
                print(f"[WRITE_COILS_DEBUG] Полученный ответ на запись coils: {response_hex} (длина: {len(response)} байт)")
                logger.debug(f"Полученный ответ на запись coils: {response_hex}")
            else:
                print(f"[WRITE_COILS_ERROR] Нет ответа от устройства на запись coils")
                logger.error("Нет ответа от устройства на запись coils")
                return False

            if len(response) < 8:
                print(f"[WRITE_COILS_ERROR] Ответ слишком короткий: {len(response)} байт (минимум 8)")
                logger.error(f"Ответ слишком короткий: {len(response)} байт")
                return False

            response_crc = (response[-2]) | (response[-1] << 8)
            calculated_crc = self._calculate_crc16(response[:-2])

            print(f"[WRITE_COILS_DEBUG] CRC записи coils: получен={response_crc:04X}, рассчитан={calculated_crc:04X}")

            if response_crc != calculated_crc:
                print(f"[WRITE_COILS_ERROR] Неверный CRC в ответе на запись coils")
                logger.error("Неверный CRC в ответе на запись coils")
                return False

            if response[0] != self.device_address:
                print(f"[WRITE_COILS_ERROR] Неверный адрес устройства в ответе: получен={response[0]}, ожидался={self.device_address}")
                logger.error(f"Неверный адрес устройства в ответе: {response[0]} != {self.device_address}")
                return False

            if response[1] != 0x0F:
                if response[1] & 0x80:
                    exception_code = response[2]
                    print(f"[WRITE_COILS_ERROR] Код исключения Modbus: {exception_code}")
                    print(f"[WRITE_COILS_DEBUG] Расшифровка кода исключения:")
                    if exception_code == 1:
                        print("  1 - Illegal Function - Функция не поддерживается")
                    elif exception_code == 2:
                        print("  2 - Illegal Data Address - Неверный адрес данных")
                    elif exception_code == 3:
                        print("  3 - Illegal Data Value - Неверное значение данных")
                    elif exception_code == 4:
                        print("  4 - Slave Device Failure - Сбой устройства")
                    elif exception_code == 5:
                        print("  5 - Acknowledge - Подтверждение (длительная операция)")
                    elif exception_code == 6:
                        print("  6 - Slave Device Busy - Устройство занято")
                    else:
                        print(f"  {exception_code} - Неизвестный код исключения")
                    logger.error(f"Код исключения Modbus: {exception_code}")
                    return False
                else:
                    print(f"[WRITE_COILS_ERROR] Неверная функция в ответе: получена={response[1]:02X}, ожидалась=0F")
                    logger.error(f"Неверная функция в ответе: {response[1]:02X} != 0F")
                    return False

            response_start = (response[2] << 8) | response[3]
            response_count = (response[4] << 8) | response[5]

            print(f"[WRITE_COILS_DEBUG] Проверка ответа: адрес {response_start} (ожидался {start_address}), количество {response_count} (ожидалось {count})")

            if response_start != start_address or response_count != count:
                print(f"[WRITE_COILS_WARNING] Несоответствие в ответе: адрес {response_start} != {start_address}, количество {response_count} != {count}")
                logger.warning(f"Несоответствие в ответе: адрес {response_start} != {start_address}, количество {response_count} != {count}")

            print(f"[WRITE_COILS_SUCCESS] Успешно записано {count} coils начиная с адреса {start_address}")
            logger.info(f"Успешно записано {count} coils начиная с адреса {start_address}")
            return True

        except Exception as e:
            print(f"[WRITE_COILS_ERROR] Исключение при записи coils: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Исключение при записи coils: {e}")
            return False

    def _calculate_crc16(self, data: Union[bytes, bytearray]) -> int:
        """
        Вычисляет CRC16 для Modbus RTU

        Args:
            data: Данные для вычисления CRC

        Returns:
            int: CRC16 значение
        """
        crc = 0xFFFF

        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1

        return crc
