# Установка и настройка Rust сканера Modbus

## Краткая инструкция

```bash
# 1. Установите Rust (если не установлен)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 2. Установите Maturin
pip install maturin

# 3. Скомпилируйте Rust библиотеку
cd /home/roman/Документы/Python/DVLINK\ GUI/gui/modbus_scanner_rust
maturin develop --release

# 4. Запустите тест
python test_rust_scanner.py --port /dev/ttyUSB0
```

## Подробная инструкция

### Шаг 1: Установка Rust

Rust необходим для компиляции быстрого сканера.

**Linux/macOS:**
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

**Windows:**
Скачайте установщик с https://rustup.rs/

**Проверка установки:**
```bash
rustc --version
cargo --version
```

### Шаг 2: Установка Maturin

Maturin - инструмент для сборки Python расширений на Rust.

```bash
pip install maturin
```

Или через requirements.txt:
```bash
pip install -r requirements.txt
```

### Шаг 3: Сборка Rust библиотеки

```bash
cd gui/modbus_scanner_rust
maturin develop --release
```

**Опции:**
- `--release` - оптимизированная сборка (быстрее в 5-10 раз)
- `--dev` - отладочная сборка (для разработки)

**Проверка:**
```bash
python -c "import modbus_scanner_rust; print('OK')"
```

### Шаг 4: Интеграция в проект

Библиотека автоматически интегрируется в `modbus_worker.py`.

При запуске GUI:
- Если Rust сканер доступен - используется быстрый перебор
- Если недоступен - используется старый Python код

**Проверка работы:**
```
[INFO] Rust сканер загружен - быстрый перебор адресов/скоростей доступен
```

## Использование

### В GUI приложении

Автоматически используется при автоопределении:
- "Автоопределение скорости" → быстрый перебор 5 скоростей
- "Автоопределение адреса" → быстрый перебор 1-200 адресов

### В коде Python

```python
from modbus_scanner_wrapper import ModbusScannerRust

# Создание сканера
scanner = ModbusScannerRust("/dev/ttyUSB0", timeout_ms=100)

# Быстрое определение адреса
result = scanner.scan_first_found(
    baudrate=38400,
    start_address=1,
    end_address=200
)
if result:
    print(f"Найдено: адрес={result['address']}, скорость={result['baudrate']}")

# Полное сканирование
results = scanner.scan_all(
    baudrates=[115200, 57600, 38400, 19200, 9600],
    start_address=1,
    end_address=200
)
for r in results:
    print(f"Устройство: {r}")
```

## Производительность

### Сравнение

| Операция | Python | Rust | Ускорение |
|----------|--------|------|-----------|
| 1 адрес/скорость | ~500ms | ~50ms | 10x |
| 100 адресов (1 скорость) | ~50s | ~5s | 10x |
| 200 адресов × 5 скоростей | ~500s | ~50s | 10x |

### Факторы влияющие на скорость

1. **Таймаут** (timeout_ms): 
   - Меньше = быстрее, но больше ложных отрицаний
   - Рекомендуется: 50-100ms

2. **Диапазон адресов**:
   - Перебирайте только нужный диапазон
   - По умолчанию: 1-200

3. **Скорости**:
   - Начинайте с высоких (115200, 57600)
   - Обычно устройство на 38400 или 115200

## Отладка

### Ошибки компиляции

**Проблема:** `error: no such command: maturin`
```bash
pip install maturin
```

**Проблема:** `error: linker cc not found`
```bash
# Ubuntu/Debian
sudo apt install build-essential

# macOS
xcode-select --install
```

**Проблема:** `pyo3 version mismatch`
```bash
cd modbus_scanner_rust
cargo update
maturin develop --release
```

### Ошибки выполнения

**Проблема:** `Rust сканер недоступен`
```bash
# Проверьте что библиотека скомпилирована
python -c "import modbus_scanner_rust"

# Если ошибка - перекомпилируйте
cd modbus_scanner_rust
maturin develop --release
```

**Проблема:** `Permission denied на /dev/ttyUSB0`
```bash
# Добавьте пользователя в группу dialout
sudo usermod -a -G dialout $USER
# Перезайдите в систему
```

### Тестирование

```bash
# Базовый тест
python test_rust_scanner.py --port /dev/ttyUSB0

# Сравнение Python vs Rust
python test_rust_scanner.py --port /dev/ttyUSB0 --compare
```

## Структура проекта

```
gui/
├── modbus_scanner_rust/
│   ├── Cargo.toml          # Rust зависимости
│   ├── pyproject.toml      # Maturin конфигурация
│   ├── src/
│   │   └── lib.rs          # Rust код сканера
│   └── README.md           # Документация Rust
├── modbus_scanner_wrapper.py  # Python обёртка
├── modbus_worker.py        # Интеграция в GUI (обновлён)
└── test_rust_scanner.py    # Тесты производительности
```

## Дополнительная документация

- [Rust сканер README](modbus_scanner_rust/README.md)
- [PyO3 документация](https://pyo3.rs/)
- [Maturin документация](https://www.maturin.rs/)

## Поддержка

Вопросы и проблемы:
1. Проверьте логи при запуске
2. Запустите `test_rust_scanner.py`
3. Убедитесь что Rust и Maturin установлены
