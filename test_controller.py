#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Controller Module
Класс для управления тестированием устройства Modbus
"""

import sys
import os
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import (
    TEST_MODES, TIMER_INTERVALS, COIL_ADDRESSES
)


class TestController:
    """Класс для управления тестированием устройства"""

    def __init__(self, worker_thread, log_callback=None):
        """
        Инициализация контроллера тестирования

        Args:
            worker_thread: Экземпляр ModbusWorkerThread
            log_callback: Функция для логирования сообщений
        """
        self.worker_thread = worker_thread
        self.log_callback = log_callback or self._default_log

        # Состояние тестирования
        self.test_mode = TEST_MODES["FULL_SWITCH"]
        self.auto_testing_active = False
        self.full_switch_state = False  # False = все выключено, True = все включено

        # Состояние бегущих огней
        self.running_lights_active = False
        self.running_lights_step = 0
        self.running_lights_timer = None

        # Состояние змейки
        self.snake_active = False
        self.snake_step = 0
        self.snake_timer = None

        # Таймер автоматического тестирования
        self.auto_test_timer = QTimer()
        self.auto_test_timer.timeout.connect(self.run_auto_test_cycle)
        self.auto_test_timer.setInterval(TIMER_INTERVALS["AUTO_TEST"])

    def _default_log(self, message: str):
        """Функция логирования по умолчанию"""
        print(f"[TEST] {message}")

    def set_test_mode(self, mode: str):
        """Установить режим тестирования"""
        if mode in TEST_MODES.values():
            self.test_mode = mode
            self.log_callback(f"[MODE] Режим тестирования изменен на: {mode}")
            self.stop_all_tests()
        else:
            self.log_callback(f"[ERROR] Неизвестный режим тестирования: {mode}")

    def run_test(self, mode: str = None, auto: bool = False):
        """
        Запустить тестирование

        Args:
            mode: Режим тестирования (если None, используется текущий)
            auto: Автоматическое тестирование
        """
        if not self.worker_thread or not self.worker_thread.is_connected:
            QMessageBox.warning(None, "Ошибка", "Сначала подключитесь к устройству")
            return

        test_mode = mode or self.test_mode

        # Если автоматическое тестирование уже активно - остановить его и выполнить один цикл
        if self.auto_testing_active:
            self.log_callback(f"[TEST] Остановка автоматического тестирования и выполнение одного цикла режима '{test_mode}'")
            self.stop_auto_testing()

            # Выполняем один шаг в зависимости от режима
            if test_mode == TEST_MODES["RUNNING_LIGHTS"]:
                self.running_lights_next_step()
            elif test_mode == TEST_MODES["FULL_SWITCH"]:
                self.run_full_switch_test()
            elif test_mode == TEST_MODES["SNAKE"]:
                self.snake_next_step()
        else:
            # Обычная логика запуска
            self.log_callback(f"Запуск теста: режим '{test_mode}', автоматическое тестирование: {auto}")

            # Выполняем тест в зависимости от режима
            if test_mode == TEST_MODES["RUNNING_LIGHTS"]:
                self.run_running_lights_test()
            elif test_mode == TEST_MODES["FULL_SWITCH"]:
                self.run_full_switch_test()
            elif test_mode == TEST_MODES["SNAKE"]:
                self.run_snake_test()

            # Если автоматическое тестирование включено, запускаем таймер
            if auto and not self.auto_testing_active:
                self.start_auto_testing()

    def run_running_lights_test(self):
        """Тестирование режима бегущих огней (бегущий огонь с 3 активными катушками)"""
        self.log_callback("[TEST] Выполнение теста: Режим бегущие огни")

        if not self.worker_thread or not self.worker_thread.is_connected:
            QMessageBox.warning(None, "Ошибка", "Сначала подключитесь к устройству")
            return

        # Получаем значения каналов (предполагаем, что они доступны через worker или config)
        # В реальной реализации это нужно передать как параметры
        channel1_value = getattr(self, 'channel1_value', 0)
        channel2_value = getattr(self, 'channel2_value', 0)

        self.log_callback(f"[TEST] Канал 1: {channel1_value} катушек (coils 0-{channel1_value-1})")
        self.log_callback(f"[TEST] Канал 2: {channel2_value} катушек (coils 32-{32+channel2_value-1})")

        # Проверяем минимальные значения
        if channel1_value < 3:
            QMessageBox.warning(None, "Ошибка", "Канал 1 должен иметь минимум 3 катушки")
            return
        if channel2_value < 3:
            QMessageBox.warning(None, "Ошибка", "Канал 2 должен иметь минимум 3 катушки")
            return

        # Запускаем тест
        self.running_lights_active = True
        self.running_lights_step = 0

        # Создаем таймер для последовательного выполнения шагов
        if self.running_lights_timer:
            self.running_lights_timer.stop()
        self.running_lights_timer = QTimer()
        self.running_lights_timer.timeout.connect(self.running_lights_next_step)
        self.running_lights_timer.setInterval(TIMER_INTERVALS["RUNNING_LIGHTS"])
        self.running_lights_timer.start()

        self.log_callback("[TEST] Запуск бегущего огня...")

    def running_lights_next_step(self):
        """Выполнить следующий шаг бегущего огня"""
        if not self.running_lights_active:
            return

        channel1_value = getattr(self, 'channel1_value', 0)
        channel2_value = getattr(self, 'channel2_value', 0)

        # Количество шагов для каждого канала
        max_steps_channel1 = channel1_value - 2
        max_steps_channel2 = channel2_value - 2

        # Определяем текущий шаг для каждого канала
        step1 = self.running_lights_step % max_steps_channel1
        step2 = self.running_lights_step % max_steps_channel2

        # Канал 1: coils 0 to channel1_value-1
        channel1_coils = [False] * channel1_value
        if step1 < max_steps_channel1:
            channel1_coils[step1] = True
            channel1_coils[step1 + 1] = True
            channel1_coils[step1 + 2] = True

        # Канал 2: coils 32 to 32+channel2_value-1
        channel2_coils = [False] * channel2_value
        if step2 < max_steps_channel2:
            channel2_coils[step2] = True
            channel2_coils[step2 + 1] = True
            channel2_coils[step2 + 2] = True

        # Отправляем coils для канала 1
        if channel1_coils and self.worker_thread:
            result1 = self.worker_thread.write_coils(COIL_ADDRESSES["CHANNEL1_START"], channel1_coils)
            if result1 and result1.get("status") == "success":
                active_coils1 = [i for i, v in enumerate(channel1_coils) if v]
                self.log_callback(f"[TEST] Канал 1: активные coils {active_coils1}")
            else:
                self.log_callback("[TEST] Ошибка записи coils для Канала 1")

        # Отправляем coils для канала 2
        if channel2_coils and self.worker_thread:
            result2 = self.worker_thread.write_coils(COIL_ADDRESSES["CHANNEL2_START"], channel2_coils)
            if result2 and result2.get("status") == "success":
                active_coils2 = [COIL_ADDRESSES["CHANNEL2_START"] + i for i, v in enumerate(channel2_coils) if v]
                self.log_callback(f"[TEST] Канал 2: активные coils {active_coils2}")
            else:
                self.log_callback("[TEST] Ошибка записи coils для Канала 2")

        # Увеличиваем шаг
        self.running_lights_step += 1

        # Проверяем, нужно ли остановить тест (после нескольких циклов)
        if self.running_lights_step >= max(max_steps_channel1, max_steps_channel2) * 3:  # 3 цикла
            self.stop_running_lights_test()

    def stop_running_lights_test(self):
        """Остановить тест бегущих огней"""
        self.running_lights_active = False
        if self.running_lights_timer:
            self.running_lights_timer.stop()
            self.running_lights_timer = None

        # Выключаем все coils
        channel1_value = getattr(self, 'channel1_value', 0)
        channel2_value = getattr(self, 'channel2_value', 0)

        if channel1_value > 0 and self.worker_thread:
            self.worker_thread.write_coils(COIL_ADDRESSES["CHANNEL1_START"], [False] * channel1_value)
        if channel2_value > 0 and self.worker_thread:
            self.worker_thread.write_coils(COIL_ADDRESSES["CHANNEL2_START"], [False] * channel2_value)

        self.log_callback("[TEST] Тест бегущих огней завершен")

    def run_full_switch_test(self):
        """Тестирование режима полного переключения (все coils ON/OFF по нажатию)"""
        self.log_callback("[TEST] Выполнение теста: Режим полного переключения")

        if not self.worker_thread or not self.worker_thread.is_connected:
            QMessageBox.warning(None, "Ошибка", "Сначала подключитесь к устройству")
            return

        channel1_value = getattr(self, 'channel1_value', 0)
        channel2_value = getattr(self, 'channel2_value', 0)

        self.log_callback(f"[TEST] Канал 1: {channel1_value} катушек (coils 0-{channel1_value-1})")
        self.log_callback(f"[TEST] Канал 2: {channel2_value} катушек (coils 32-{32+channel2_value-1})")

        # Переключаем состояние
        if self.full_switch_state:
            new_state = False
            self.full_switch_state = False
            self.log_callback("[TEST] Выключение всех coils")
        else:
            new_state = True
            self.full_switch_state = True
            self.log_callback("[TEST] Включение всех coils")

        # Создаем списки значений для coils
        channel1_coils = [new_state] * channel1_value if channel1_value > 0 else []
        channel2_coils = [new_state] * channel2_value if channel2_value > 0 else []

        # Отправляем coils для канала 1
        if channel1_coils:
            result1 = self.worker_thread.write_coils(COIL_ADDRESSES["CHANNEL1_START"], channel1_coils)
            if result1 and result1.get("status") == "success":
                state_text = "ON" if new_state else "OFF"
                self.log_callback(f"[TEST] Канал 1: все coils установлены в {state_text}")
            else:
                self.log_callback("[TEST] Ошибка записи coils для Канала 1")

        # Отправляем coils для канала 2
        if channel2_coils:
            result2 = self.worker_thread.write_coils(COIL_ADDRESSES["CHANNEL2_START"], channel2_coils)
            if result2 and result2.get("status") == "success":
                state_text = "ON" if new_state else "OFF"
                self.log_callback(f"[TEST] Канал 2: все coils установлены в {state_text}")
            else:
                self.log_callback("[TEST] Ошибка записи coils для Канала 2")

        self.log_callback(f"[TEST] Текущее состояние: {'ВКЛЮЧЕНО' if self.full_switch_state else 'ВЫКЛЮЧЕНО'}")

    def run_snake_test(self):
        """Тестирование режима змейка (последовательное включение всех coils)"""
        self.log_callback("[TEST] Выполнение теста: Режим змейка")

        if not self.worker_thread or not self.worker_thread.is_connected:
            QMessageBox.warning(None, "Ошибка", "Сначала подключитесь к устройству")
            return

        channel1_value = getattr(self, 'channel1_value', 0)
        channel2_value = getattr(self, 'channel2_value', 0)

        self.log_callback(f"[TEST] Канал 1: {channel1_value} катушек (coils 0-{channel1_value-1})")
        self.log_callback(f"[TEST] Канал 2: {channel2_value} катушек (coils 32-{32+channel2_value-1})")

        # Проверяем минимальные значения
        if channel1_value < 1:
            QMessageBox.warning(None, "Ошибка", "Канал 1 должен иметь минимум 1 катушку")
            return
        if channel2_value < 1:
            QMessageBox.warning(None, "Ошибка", "Канал 2 должен иметь минимум 1 катушку")
            return

        # Запускаем тест
        self.snake_active = True
        self.snake_step = 0

        # Создаем таймер для последовательного включения
        if self.snake_timer:
            self.snake_timer.stop()
        self.snake_timer = QTimer()
        self.snake_timer.timeout.connect(self.snake_next_step)
        self.snake_timer.setInterval(TIMER_INTERVALS["SNAKE"])
        self.snake_timer.start()

        self.log_callback("[TEST] Запуск змейки...")

    def snake_next_step(self):
        """Выполнить следующий шаг змейки"""
        if not self.snake_active:
            return

        channel1_value = getattr(self, 'channel1_value', 0)
        channel2_value = getattr(self, 'channel2_value', 0)

        # Создаем списки coils для текущего шага
        # Включаем coils от 0 до snake_step
        channel1_coils = [i <= self.snake_step for i in range(channel1_value)]
        channel2_coils = [i <= self.snake_step for i in range(channel2_value)]

        # Отправляем coils для канала 1
        if channel1_coils and self.worker_thread:
            result1 = self.worker_thread.write_coils(COIL_ADDRESSES["CHANNEL1_START"], channel1_coils)
            if result1 and result1.get("status") == "success":
                active_coils1 = [i for i, v in enumerate(channel1_coils) if v]
                self.log_callback(f"[TEST] Канал 1: активные coils {active_coils1}")
            else:
                self.log_callback("[TEST] Ошибка записи coils для Канала 1")

        # Отправляем coils для канала 2
        if channel2_coils and self.worker_thread:
            result2 = self.worker_thread.write_coils(COIL_ADDRESSES["CHANNEL2_START"], channel2_coils)
            if result2 and result2.get("status") == "success":
                active_coils2 = [COIL_ADDRESSES["CHANNEL2_START"] + i for i, v in enumerate(channel2_coils) if v]
                self.log_callback(f"[TEST] Канал 2: активные coils {active_coils2}")
            else:
                self.log_callback("[TEST] Ошибка записи coils для Канала 2")

        # Увеличиваем шаг
        self.snake_step += 1

        # Проверяем, нужно ли сбросить (все coils включены)
        if self.snake_step >= max(channel1_value, channel2_value):
            self.log_callback("[TEST] Все coils включены - сброс и повтор")
            self.snake_step = 0  # Сбрасываем шаг

    def stop_snake_test(self):
        """Остановить тест змейки"""
        self.snake_active = False
        if self.snake_timer:
            self.snake_timer.stop()
            self.snake_timer = None

        # Выключаем все coils
        channel1_value = getattr(self, 'channel1_value', 0)
        channel2_value = getattr(self, 'channel2_value', 0)

        if channel1_value > 0 and self.worker_thread:
            self.worker_thread.write_coils(COIL_ADDRESSES["CHANNEL1_START"], [False] * channel1_value)
        if channel2_value > 0 and self.worker_thread:
            self.worker_thread.write_coils(COIL_ADDRESSES["CHANNEL2_START"], [False] * channel2_value)

        self.log_callback("[TEST] Тест змейки остановлен")

    def run_auto_test_cycle(self):
        """Циклическое выполнение автоматического тестирования"""
        if not self.worker_thread or not self.worker_thread.is_connected:
            self.stop_auto_testing()
            return

        # Определяем текущий режим и выполняем тест
        if self.test_mode == TEST_MODES["RUNNING_LIGHTS"]:
            self.run_running_lights_test()
        elif self.test_mode == TEST_MODES["FULL_SWITCH"]:
            self.run_full_switch_test()
        elif self.test_mode == TEST_MODES["SNAKE"]:
            self.run_snake_test()

    def start_auto_testing(self):
        """Запуск автоматического тестирования"""
        if self.auto_testing_active:
            return

        self.auto_testing_active = True
        self.auto_test_timer.start()
        self.log_callback("[AUTO TEST] Автоматическое тестирование запущено")

    def stop_auto_testing(self):
        """Остановка автоматического тестирования"""
        if not self.auto_testing_active:
            return

        self.auto_testing_active = False
        self.auto_test_timer.stop()
        self.log_callback("[AUTO TEST] Автоматическое тестирование остановлено")

    def stop_all_tests(self):
        """Остановить все активные тесты"""
        # Останавливаем тест бегущих огней
        if self.running_lights_active:
            self.stop_running_lights_test()

        # Останавливаем тест змейки
        if self.snake_active:
            self.stop_snake_test()

        # Останавливаем автоматическое тестирование
        if self.auto_testing_active:
            self.stop_auto_testing()

        # Сбрасываем состояние полного переключения
        self.full_switch_state = False

        # Выключаем все coils
        channel1_value = getattr(self, 'channel1_value', 0)
        channel2_value = getattr(self, 'channel2_value', 0)

        if channel1_value > 0 and self.worker_thread:
            self.worker_thread.write_coils(COIL_ADDRESSES["CHANNEL1_START"], [False] * channel1_value)
        if channel2_value > 0 and self.worker_thread:
            self.worker_thread.write_coils(COIL_ADDRESSES["CHANNEL2_START"], [False] * channel2_value)

        self.log_callback("[MODE] Все тесты остановлены, coils выключены")

    def set_channel_values(self, channel1: int, channel2: int):
        """Установить значения каналов для тестирования"""
        self.channel1_value = channel1
        self.channel2_value = channel2