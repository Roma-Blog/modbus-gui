# Кроссплатформенность Linux + Windows

## Внесённые изменения

Этот документ описывает все изменения, сделанные для обеспечения кроссплатформенности приложения.

---

## 1. USB Monitor (`wizard/usb_monitor.py`)

**Проблема:** `pyudev` работает только на Linux

**Решение:** Добавлены 3 режима работы:

| Режим | Платформа | Описание |
|-------|-----------|----------|
| Linux udev | Linux + pyudev | События подключения/отключения (мгновенно) |
| Linux polling | Linux без pyudev | Опрос списка портов (1 сек) |
| Windows polling | Windows | Опрос списка портов (1 сек) |

**Изменения:**
- Добавлено определение платформы через `sys.platform`
- Добавлен метод `_run_windows_mode()` для Windows
- Добавлен метод `_run_linux_polling_mode()` для Linux без pyudev
- Обновлён `__init__` с параметром `poll_interval_ms`

---

## 2. Constants (`constants.py`)

**Проблема:** Жёстко заданные порты только для Linux

**Решение:** Динамический выбор портов по умолчанию:

```python
if IS_WINDOWS:
    DEFAULT_COM_PORTS = ["COM1", "COM2", "COM3", ...]
elif IS_MACOS:
    DEFAULT_COM_PORTS = ["/dev/cu.usbserial-1", ...]
else:  # Linux
    DEFAULT_COM_PORTS = ["/dev/ttyUSB0", "/dev/ttyACM0", ...]
```

**Изменения:**
- Добавлены константы `IS_WINDOWS`, `IS_LINUX`, `IS_MACOS`
- Обновлён `DEFAULT_COM_PORTS` для каждой платформы

---

## 3. Step Connect (`wizard/step_connect.py`)

**Проблема:** Жёстко заданные порты в `scan_ports()`

**Решение:** Использование `DEFAULT_COM_PORTS` из `constants`

**Изменения:**
- Заменён список портов на импорт из `constants`
- Убрано исключение для `USBMonitor` (теперь кроссплатформенный)

---

## 4. Requirements (`requirements.txt`)

**Проблема:** `pyudev` не устанавливается на Windows

**Решение:** Условные зависимости:

```txt
# Опционально: для Linux
pyudev>=0.21.0; sys_platform == 'linux'

# Опционально: для Windows
pywin32>=305; sys_platform == 'win32'
```

---

## 5. PyInstaller Spec (`modbus_gui_wizard.spec`)

**Проблема:** Нет spec файла для сборки Wizard

**Решение:** Создан новый spec файл с:
- Автоматическим поиском Rust библиотеки (.so или .pyd)
- Кроссплатформенными hiddenimports
- Опциональной иконкой

---

## 6. Документация

### Созданные файлы:

- `BUILD_WINDOWS.md` - Инструкция по сборке для Windows
- `CROSS_PLATFORM.md` - Этот файл

### Обновлённые файлы:

- `README.md` - Добавлена таблица кроссплатформенности
- `modbus_scanner_rust/README.md` - Добавлены инструкции для Windows

---

## Тестирование

### Linux

```bash
source .venv/bin/activate
python __main__.py
```

### Windows (в VM или на реальном устройстве)

```powershell
.venv\Scripts\Activate
python __main__.py
```

### Проверка импортов

```bash
python -c "
from constants import IS_WINDOWS, IS_LINUX, DEFAULT_COM_PORTS
from wizard.usb_monitor import USBMonitor
import serial.tools.list_ports
print('✅ Все импорты успешны!')
"
```

---

## Сборка

### Linux

```bash
pip install pyinstaller
pyinstaller --clean modbus_gui_wizard.spec
```

### Windows

```powershell
pip install pyinstaller
pyinstaller --clean modbus_gui_wizard.spec
```

---

## Известные ограничения

| Компонент | Linux | Windows | macOS |
|-----------|-------|---------|-------|
| USB мониторинг (udev) | ✅ | ❌ | ❌ |
| USB мониторинг (polling) | ✅ | ✅ | ✅ |
| COM порты | ✅ | ✅ | ⚠️ |
| Rust сканер | ✅ | ✅ | ⚠️ |
| GUI (PyQt5) | ✅ | ✅ | ⚠️ |

**Примечания:**
- macOS требует тестирования
- На Windows может потребоваться установка Visual C++ Redistributable
- Для работы с COM портами на Windows могут потребоваться драйверы устройства

---

## Чеклист для Windows сборки

- [ ] Установлен Python 3.8+
- [ ] Установлен Rust (rustup или winget)
- [ ] Установлен Maturin: `pip install maturin`
- [ ] Скомпилирован `modbus_scanner_rust`: `maturin develop --release`
- [ ] Проверен импорт: `python -c "import modbus_scanner_rust"`
- [ ] Установлен PyInstaller: `pip install pyinstaller`
- [ ] Собрано приложение: `pyinstaller modbus_gui_wizard.spec`
- [ ] Протестирован запуск `.exe` файла

---

## Миграция со старой версии

Если вы обновляетесь с версии только для Linux:

1. Обновите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

2. Перекомпилируйте Rust модуль (если нужно):
   ```bash
   cd modbus_scanner_rust && maturin develop --release
   ```

3. Проверьте что приложение запускается:
   ```bash
   python __main__.py
   ```

4. Для сборки используйте новый spec файл:
   ```bash
   pyinstaller modbus_gui_wizard.spec
   ```
