#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modbus Device Info Module
Модуль для чтения информации об устройстве
"""

import time
import logging
from typing import Optional, Union
import serial

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    force=True)
logger = logging.getLogger(__name__)

class ModbusDeviceInfo:
    """Класс для чтения информации об устройстве Modbus"""

    def __init__(self, connection: serial.Serial, device_address: int):
        """
        Инициализация

        Args:
            connection: Активное соединение
            device_address: Адрес Modbus устройства (1-247)
        """
        self.connection = connection
        self.device_address = device_address

    def get_device_info(self) -> Optional[dict]:
        """
        Получает информацию об устройстве командой 17

        Returns:
            dict или None: Информация об устройстве
        """
        try:
            if not self.connection:
                logger.error("Соединение не инициализировано")
                return None

            if hasattr(self.connection, 'is_open'):
                if not self.connection.is_open:
                    logger.error("Соединение закрыто")
                    return None
            else:
                try:
                    self.connection.write(b'\x00')
                    self.connection.flush()
                except:
                    logger.error("Соединение недоступно")
                    return None

            return self._send_modbus_command_17(self.connection)

        except KeyboardInterrupt:
            logger.info("Получение информации прервано пользователем")
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении информации об устройстве: {e}")
            return None

    def _send_modbus_command_17(self, connection: serial.Serial) -> Optional[dict]:
        """
        Отправляет команду Modbus 17 (Read Device Identification)

        Args:
            connection: Активное соединение

        Returns:
            dict или None: Данные устройства или None при ошибке
        """
        try:
            request = bytearray([
                self.device_address,
                0x11,
                0x00,
                0x00,
                0x00,
                0x00
            ])

            crc = self._calculate_crc16(request)
            request.extend([crc & 0xFF, (crc >> 8) & 0xFF])

            try:
                connection.write(request)
                connection.flush()
            except Exception as e:
                logger.error(f"Ошибка при отправке запроса: {e}")
                return None

            time.sleep(0.1)

            try:
                response = connection.read(100)
            except Exception as e:
                logger.error(f"Ошибка при чтении ответа: {e}")
                return None

            if len(response) < 7:
                return None

            if len(response) >= 2:
                response_crc = (response[-2]) | (response[-1] << 8)
                calculated_crc = self._calculate_crc16(response[:-2])

                if response_crc != calculated_crc:
                    logger.warning(f"Неверный CRC в ответе: получен 0x{response_crc:04X}, ожидался 0x{calculated_crc:04X}")
                    logger.info("Попытка повторного чтения...")
                    time.sleep(0.2)
                    for retry_count in range(2):
                        response = connection.read(100)
                        if len(response) >= 2:
                            response_crc = (response[-2]) | (response[-1] << 8)
                            calculated_crc = self._calculate_crc16(response[:-2])
                            if response_crc == calculated_crc:
                                logger.info(f"CRC исправлен после попытки {retry_count + 1}")
                                break
                        time.sleep(0.1)
                    else:
                        logger.debug("CRC ошибка не исправлена после повторных попыток")
                        return None
            else:
                logger.warning("Ответ слишком короткий для проверки CRC")
                return None

            if response[0] != self.device_address or response[1] != 0x11:
                logger.debug("Неверный адрес устройства или функция в ответе")
                return None

            device_data = self._parse_device_identification_response(response)

            if device_data:
                logger.debug("Короткая пауза после успешного ответа...")
                time.sleep(0.5)

            return device_data

        except Exception as e:
            logger.debug(f"Ошибка отправки команды 17: {e}")
            return None

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

    def _parse_device_identification_response(self, response: bytes) -> dict:
        """
        Парсит ответ команды Read Device Identification

        Args:
            response: Байтовый ответ от устройства

        Returns:
            dict: Распарсенные данные устройства
        """
        try:
            if len(response) < 8:
                return {"raw_response": response.hex()}

            device_info = {
                "device_address": response[0],
                "function_code": response[1],
                "mei_response": response[2],
                "read_device_id_code": response[3],
                "conformity_level": response[4],
                "more_follows": response[5],
                "next_object_id": response[6],
                "number_of_objects": response[7]
            }

            objects = {}
            pos = 8

            for i in range(device_info["number_of_objects"]):
                if pos + 2 >= len(response):
                    break

                object_id = response[pos]
                object_length = response[pos + 1]
                pos += 2

                if pos + object_length > len(response):
                    break

                object_value = response[pos:pos + object_length].decode('ascii', errors='ignore')
                objects[f"object_{object_id}"] = object_value
                pos += object_length

            device_info["objects"] = objects
            device_info["raw_response"] = response.hex()

            device_info["hex_format"] = " ".join([f"{b:02X}" for b in response])
            device_info["response_length"] = len(response)

            return device_info

        except Exception as e:
            logger.debug(f"Ошибка парсинга ответа: {e}")
            return {
                "raw_response": response.hex(),
                "hex_format": " ".join([f"{b:02X}" for b in response]),
                "response_length": len(response),
                "parse_error": str(e)
            }
