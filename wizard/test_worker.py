#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Worker Thread - Поток для асинхронного тестирования
"""

import sys
import os
import time

from PyQt5.QtCore import QThread, pyqtSignal, QTimer

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import TEST_MODES, COIL_ADDRESSES


class TestWriteWorker(QThread):
    """Поток для записи coils"""

    finished = pyqtSignal(bool, dict)  # (success, result)
    error = pyqtSignal(str)

    def __init__(self, worker_thread, start_address: int, values: list):
        super().__init__()
        self.worker_thread = worker_thread
        self.start_address = start_address
        self.values = values
        # Важно: не удалять поток после завершения
        self.finished.connect(self._on_finished)

    def _on_finished(self):
        """Обработка завершения - помечаем для удаления"""
        self.deleteLater()

    def run(self):
        """Выполнить запись coils"""
        try:
            # Небольшая задержка перед записью чтобы устройство успело подготовиться
            time.sleep(0.05)
            
            result = self.worker_thread.write_coils(self.start_address, self.values)
            
            # Даём устройству время на ответ
            time.sleep(0.1)
            
            if result and result.get("status") == "success":
                self.finished.emit(True, result)
            else:
                self.finished.emit(False, result or {})
        except Exception as e:
            self.error.emit(str(e))
        finally:
            # Гарантированно вызываем deleteLater
            self.deleteLater()


class AsyncTestController:
    """Асинхронный контроллер тестирования"""

    def __init__(self, worker_thread, log_callback=None):
        self.worker_thread = worker_thread
        self.log_callback = log_callback or (lambda x: None)

        # Состояние
        self.test_mode = TEST_MODES["FULL_SWITCH"]
        self.auto_testing_active = False
        self.full_switch_state = False

        # Состояние бегущих огней
        self.running_lights_active = False
        self.running_lights_step = 0
        self.running_lights_timer = None
        self.channel1_value = 0
        self.channel2_value = 0

        # Состояние змейки
        self.snake_active = False
        self.snake_step = 0
        self.snake_timer = None

        # Таймер автотестов - увеличенный интервал для стабильности
        self.auto_test_timer = QTimer()
        self.auto_test_timer.timeout.connect(self.run_auto_test_cycle)
        self.auto_test_timer.setInterval(1500)  # 1.5 секунды вместо 500мс

        # Текущие worker потоки - храним ссылки
        self.current_workers = []

    def _cleanup_worker(self, worker):
        """Очистка worker после завершения"""
        if worker in self.current_workers:
            self.current_workers.remove(worker)

    def set_channel_values(self, channel1: int, channel2: int):
        """Установить значения каналов"""
        self.channel1_value = channel1
        self.channel2_value = channel2

    def run_test(self, mode: str = None, auto: bool = False):
        """Запустить тест"""
        test_mode = mode or self.test_mode

        if self.auto_testing_active:
            self.stop_auto_testing()
            # Выполняем один шаг
            if test_mode == TEST_MODES["RUNNING_LIGHTS"]:
                self._running_lights_step_async()
            elif test_mode == TEST_MODES["FULL_SWITCH"]:
                self._full_switch_async()
            elif test_mode == TEST_MODES["SNAKE"]:
                self._snake_step_async()
        else:
            self.log_callback(f"Запуск теста: режим '{test_mode}', авто: {auto}")

            if test_mode == TEST_MODES["RUNNING_LIGHTS"]:
                self._start_running_lights_async()
            elif test_mode == TEST_MODES["FULL_SWITCH"]:
                self._full_switch_async()
            elif test_mode == TEST_MODES["SNAKE"]:
                self._start_snake_async()

            if auto and not self.auto_testing_active:
                self.start_auto_testing()

    # === FULL SWITCH ===

    def _full_switch_async(self):
        """Полное переключение асинхронно"""
        self.log_callback("[TEST] Полное переключение")

        new_state = not self.full_switch_state
        self.full_switch_state = new_state
        state_text = "ON" if new_state else "OFF"

        self.log_callback(f"[TEST] Переключение всех coils в {state_text}")

        # Создаём списки coils
        channel1_coils = [new_state] * self.channel1_value if self.channel1_value > 0 else []
        channel2_coils = [new_state] * self.channel2_value if self.channel2_value > 0 else []

        # Записываем асинхронно
        self._write_coils_async(COIL_ADDRESSES["CHANNEL1_START"], channel1_coils,
                                lambda: self._write_coils_async(COIL_ADDRESSES["CHANNEL2_START"], channel2_coils, None))

    # === RUNNING LIGHTS ===

    def _start_running_lights_async(self):
        """Запустить бегущие огни"""
        if self.channel1_value < 3 or self.channel2_value < 3:
            self.log_callback("[TEST] Ошибка: нужно минимум 3 катушки на канал")
            return

        self.running_lights_active = True
        self.running_lights_step = 0

        self.log_callback("[TEST] Запуск бегущего огня...")

        # Создаем таймер - увеличенный интервал для стабильности
        if self.running_lights_timer:
            self.running_lights_timer.stop()
        self.running_lights_timer = QTimer()
        self.running_lights_timer.timeout.connect(self._running_lights_step_async)
        self.running_lights_timer.setInterval(1500)  # 1.5 секунды
        self.running_lights_timer.start()

    def _running_lights_step_async(self):
        """Шаг бегущих огней асинхронно"""
        if not self.running_lights_active:
            return

        max_steps1 = max(1, self.channel1_value - 2)
        max_steps2 = max(1, self.channel2_value - 2)

        step1 = self.running_lights_step % max_steps1
        step2 = self.running_lights_step % max_steps2

        # Канал 1
        channel1_coils = [False] * self.channel1_value
        if step1 < max_steps1:
            channel1_coils[step1] = True
            channel1_coils[step1 + 1] = True
            channel1_coils[step1 + 2] = True

        # Канал 2
        channel2_coils = [False] * self.channel2_value
        if step2 < max_steps2:
            channel2_coils[step2] = True
            channel2_coils[step2 + 1] = True
            channel2_coils[step2 + 2] = True

        # Записываем асинхронно
        self._write_coils_async(COIL_ADDRESSES["CHANNEL1_START"], channel1_coils,
                                lambda: self._write_coils_async(COIL_ADDRESSES["CHANNEL2_START"], channel2_coils, None))

        self.running_lights_step += 1

        # Остановка после 3 циклов
        if self.running_lights_step >= max(max_steps1, max_steps2) * 3:
            self._stop_running_lights_async()

    def _stop_running_lights_async(self):
        """Остановить бегущие огни"""
        self.running_lights_active = False
        if self.running_lights_timer:
            self.running_lights_timer.stop()
            self.running_lights_timer = None

        self.log_callback("[TEST] Бегущие огни остановлены")

        # Выключаем все coils
        channel1_coils = [False] * self.channel1_value
        channel2_coils = [False] * self.channel2_value
        self._write_coils_async(COIL_ADDRESSES["CHANNEL1_START"], channel1_coils,
                                lambda: self._write_coils_async(COIL_ADDRESSES["CHANNEL2_START"], channel2_coils, None))

    # === SNAKE ===

    def _start_snake_async(self):
        """Запустить змейку"""
        if self.channel1_value < 1 or self.channel2_value < 1:
            self.log_callback("[TEST] Ошибка: нужна минимум 1 катушка на канал")
            return

        self.snake_active = True
        self.snake_step = 0

        self.log_callback("[TEST] Запуск змейки...")

        # Создаем таймер - увеличенный интервал для стабильности
        if self.snake_timer:
            self.snake_timer.stop()
        self.snake_timer = QTimer()
        self.snake_timer.timeout.connect(self._snake_step_async)
        self.snake_timer.setInterval(1500)  # 1.5 секунды
        self.snake_timer.start()

    def _snake_step_async(self):
        """Шаг змейки асинхронно"""
        if not self.snake_active:
            return

        # Включаем от 0 до snake_step
        channel1_coils = [i <= self.snake_step for i in range(self.channel1_value)]
        channel2_coils = [i <= self.snake_step for i in range(self.channel2_value)]

        # Записываем асинхронно
        self._write_coils_async(COIL_ADDRESSES["CHANNEL1_START"], channel1_coils,
                                lambda: self._write_coils_async(COIL_ADDRESSES["CHANNEL2_START"], channel2_coils, None))

        self.snake_step += 1

        # Сброс после достижения максимума
        if self.snake_step >= max(self.channel1_value, self.channel2_value):
            self.log_callback("[TEST] Змейка: сброс и повтор")
            self.snake_step = 0

    def _stop_snake_async(self):
        """Остановить змейку"""
        self.snake_active = False
        if self.snake_timer:
            self.snake_timer.stop()
            self.snake_timer = None

        self.log_callback("[TEST] Змейка остановлена")

        # Выключаем все coils
        channel1_coils = [False] * self.channel1_value
        channel2_coils = [False] * self.channel2_value
        self._write_coils_async(COIL_ADDRESSES["CHANNEL1_START"], channel1_coils,
                                lambda: self._write_coils_async(COIL_ADDRESSES["CHANNEL2_START"], channel2_coils, None))

    # === Helper methods ===

    def _write_coils_async(self, start_address: int, values: list, callback=None):
        """Асинхронная запись coils"""
        if not values:
            if callback:
                callback()
            return

        worker = TestWriteWorker(self.worker_thread, start_address, values)
        self.current_workers.append(worker)
        
        # Создаём обёртку для callback с очисткой
        def on_finished(success, result):
            self._on_write_finished(success, result, callback, worker)
        
        worker.finished.connect(on_finished)
        worker.error.connect(lambda err: self._on_write_error(err, worker))
        worker.start()
        
        # Возвращаем worker для возможной отмены
        return worker

    def _on_write_finished(self, success: bool, result: dict, callback, worker):
        """Обработка завершения записи"""
        if success:
            self.log_callback(f"[OK] {result.get('message', '')}")
        else:
            self.log_callback(f"[FAIL] Ошибка записи: {result}")

        # Очищаем worker из списка
        self._cleanup_worker(worker)

        # Небольшая задержка перед следующей операцией
        if callback:
            QTimer.singleShot(200, callback)  # 200мс задержка

    def _on_write_error(self, error: str, worker):
        """Обработка ошибки записи"""
        self.log_callback(f"[FAIL] Ошибка: {error}")
        self._cleanup_worker(worker)

    # === Auto testing ===

    def start_auto_testing(self):
        """Запуск автотестов"""
        if self.auto_testing_active:
            return
        self.auto_testing_active = True
        self.auto_test_timer.start()
        self.log_callback("[AUTO TEST] Запущено")

    def stop_auto_testing(self):
        """Остановка автотестов"""
        if not self.auto_testing_active:
            return
        self.auto_testing_active = False
        self.auto_test_timer.stop()
        self.log_callback("[AUTO TEST] Остановлено")

    def run_auto_test_cycle(self):
        """Цикл автотеста"""
        if not self.worker_thread or not self.worker_thread.is_connected:
            self.stop_auto_testing()
            return

        if self.test_mode == TEST_MODES["RUNNING_LIGHTS"]:
            self._running_lights_step_async()
        elif self.test_mode == TEST_MODES["FULL_SWITCH"]:
            self._full_switch_async()
        elif self.test_mode == TEST_MODES["SNAKE"]:
            self._snake_step_async()

    def stop_all_tests(self):
        """Остановить все тесты"""
        if self.running_lights_active:
            self._stop_running_lights_async()
        if self.snake_active:
            self._stop_snake_async()
        self.stop_auto_testing()
        self.full_switch_state = False
        
        # Ждём завершения всех worker потоков
        for worker in self.current_workers[:]:  # Копия списка
            if worker.isRunning():
                worker.wait(1000)  # Ждём до 1 секунды
        self.current_workers.clear()
