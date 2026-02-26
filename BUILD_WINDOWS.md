# DVLINK GUI - Сборка для Windows

## Требования

### 1. Python 3.8+
Скачайте с https://python.org или установите через winget:
```powershell
winget install Python.Python.3.12
```

### 2. Rust Toolchain
Необходим для компиляции `modbus_scanner_rust`:
```powershell
winget install Rustlang.Rust.MSVC
```

Или скачайте с https://rustup.rs/

### 3. Установка зависимостей
```powershell
# Создайте виртуальное окружение
python -m venv .venv

# Активируйте
.venv\Scripts\Activate

# Установите зависимости
pip install -r requirements.txt
pip install pyinstaller
```

## Сборка Rust модуля

```powershell
cd modbus_scanner_rust
maturin develop --release
cd ..
```

Проверка что модуль скомпилирован:
```powershell
python -c "import modbus_scanner_rust; print('OK')"
```

## Тестовый запуск

```powershell
.venv\Scripts\Activate
python __main__.py
```

## Сборка через PyInstaller

### Вариант 1: Через spec файл (рекомендуется)
```powershell
.venv\Scripts\Activate
pyinstaller --clean modbus_gui_wizard.spec
```

### Вариант 2: Через командную строку
```powershell
pyinstaller --clean --windowed ^
    --name DVLINK_GUI ^
    --add-data "modbus_gui_settings.json;." ^
    --hidden-import wizard.wizard_main ^
    --hidden-import wizard.step_connect ^
    --hidden-import wizard.step_config ^
    --hidden-import core.modbus_rtu_client ^
    --hidden-import serial.tools.list_ports ^
    --icon=icon.ico ^
    __main__.py
```

## Результат

После сборки executable файл будет в папке:
```
dist/DVLINK_GUI/DVLINK_GUI.exe
```

## Распространение

### Вариант 1: Папка с приложением
Скопируйте папку `dist/DVLINK_GUI` целиком - она содержит все необходимые файлы.

### Вариант 2: Один файл
В spec файле измените:
```python
exe = EXE(
    ...
    console=False,
    ...
)
```

На `onefile` режим:
```python
exe = EXE(
    ...
    console=False,
    upx=True,
    ...
)
```

И в COLLECT закомментируйте всё кроме `exe`.

## Возможные проблемы

### 1. `modbus_scanner_rust` не находится
Убедитесь что файл `.pyd` лежит в корне проекта:
```powershell
dir modbus_scanner_rust\*.pyd
```

### 2. Ошибка `pyudev` на Windows
Это нормально. Приложение автоматически использует fallback режим (опрос портов).

### 3. Антивирус блокирует .exe
Добавьте папку `dist/DVLINK_GUI` в исключения.

### 4. `VCRUNTIME140.dll not found`
Установите Visual C++ Redistributable:
https://aka.ms/vs/17/release/vc_redist.x64.exe

## Сборка для Linux

```bash
# Установка зависимостей
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller

# Сборка Rust модуля
cd modbus_scanner_rust
maturin develop --release
cd ..

# Сборка приложения
pyinstaller --clean modbus_gui_wizard.spec
```

## Кроссплатформенные особенности

| Компонент | Linux | Windows |
|-----------|-------|---------|
| USB мониторинг | pyudev (события) | Опрос портов |
| COM порты | `/dev/ttyUSB0` | `COM1`, `COM2` |
| Rust библиотека | `.so` | `.pyd` |
| Иконка | `.png` / `.svg` | `.ico` |

## Проверка на другой платформе

Для тестирования на Windows без установки:
1. Используйте VirtualBox с Windows VM
2. Или GitHub Actions для авто-сборки

Пример GitHub Actions: `.github/workflows/build-windows.yml`
