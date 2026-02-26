# 🚀 DVLINK GUI - Руководство по сборке

## Обзор

DVLINK GUI - кроссплатформенное приложение для настройки Modbus RTU устройств.

| Платформа | Статус | Файл |
|-----------|--------|------|
| Windows 10/11 | ✅ Готово | `DVLINK_GUI.exe` |
| Linux (Ubuntu/Debian) | ✅ Готово | `DVLINK_GUI` (AppImage) |
| macOS 11+ | ⚠️ Требуется тестирование | `DVLINK_GUI.app` |

---

## 📋 Требования

### Для всех платформ

- **Python 3.8+**
- **Rust toolchain** (для компиляции `modbus_scanner_rust`)
- **Maturin** (Python-Rust интеграция)

### Windows

```powershell
# Установите Python
winget install Python.Python.3.12

# Установите Rust
winget install Rustlang.Rust.MSVC

# Перезапустите PowerShell
```

### Linux (Ubuntu/Debian)

```bash
# Установите Python
sudo apt install python3 python3-venv python3-pip

# Установите Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Установите системные зависимости
sudo apt install libudev-dev libusb-1.0-0-dev
```

### macOS

```bash
# Установите Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Установите Python и Rust
brew install python rust
```

---

## 🔨 Сборка

### Автоматическая сборка (рекомендуется)

#### Windows

```powershell
# Откройте PowerShell от имени администратора
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Запустите скрипт сборки
.\build_windows.ps1
```

#### Linux

```bash
# Запустите скрипт сборки
./build_linux.sh
```

### Ручная сборка

#### Windows

```powershell
# 1. Создайте виртуальное окружение
python -m venv .venv
.venv\Scripts\Activate

# 2. Установите зависимости
pip install --upgrade pip
pip install pyserial PyQt5 maturin pyinstaller

# 3. Скомпилируйте Rust модуль
cd modbus_scanner_rust
maturin develop --release
cd ..

# 4. Проверьте модуль
python -c "import modbus_scanner_rust; print('OK')"

# 5. Соберите приложение
pyinstaller --clean modbus_gui_wizard.spec

# 6. Результат в dist\DVLINK_GUI\
```

#### Linux

```bash
# 1. Создайте виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate

# 2. Установите зависимости
pip install --upgrade pip
pip install pyserial PyQt5 maturin pyinstaller pyudev

# 3. Скомпилируйте Rust модуль
cd modbus_scanner_rust
maturin develop --release
cd ..

# 4. Проверьте модуль
python -c "import modbus_scanner_rust; print('OK')"

# 5. Соберите приложение
pyinstaller --clean modbus_gui_wizard.spec

# 6. Результат в dist/DVLINK_GUI/
```

---

## 📦 Результат сборки

После успешной сборки:

```
dist/
└── DVLINK_GUI/
    ├── DVLINK_GUI.exe      # Windows
    ├── DVLINK_GUI          # Linux
    ├── python312.dll       # Windows
    ├── PyQt5/              # Библиотеки Qt
    ├── modbus_scanner_rust.pyd  # Rust модуль (Windows)
    └── modbus_scanner_rust.so   # Rust модуль (Linux)
```

### Создание дистрибутива

#### Windows (ZIP)

```powershell
cd dist
Compress-Archive -Path DVLINK_GUI -DestinationPath DVLINK_GUI_Windows.zip
```

#### Linux (tar.gz)

```bash
cd dist
tar -czf DVLINK_GUI_Linux.tar.gz DVLINK_GUI/
```

---

## 🎯 GitHub Actions (автоматическая сборка)

Для автоматической сборки при релизе:

1. Создайте тег: `git tag v1.0.0 && git push origin v1.0.0`
2. GitHub Actions автоматически:
   - Соберёт Windows `.exe`
   - Соберёт Linux AppImage
   - Соберёт macOS `.app`
   - Создаст релиз на GitHub

Файл workflow: `.github/workflows/build.yml`

---

## ❓ Troubleshooting

### `modbus_scanner_rust` не находится

```bash
# Перекомпилируйте Rust модуль
cd modbus_scanner_rust
maturin develop --release
cd ..
```

### Ошибка `VCRUNTIME140.dll` на Windows

Установите Visual C++ Redistributable:
- https://aka.ms/vs/17/release/vc_redist.x64.exe

### Ошибка `libudev` на Linux

```bash
sudo apt install libudev-dev
```

### PyInstaller не находит модули

Добавьте в spec файл:
```python
hiddenimports=['serial.tools.list_ports']
```

### Приложение не запускается на Linux

Проверьте права доступа:
```bash
chmod +x dist/DVLINK_GUI/DVLINK_GUI
```

### Ошибка доступа к COM порту на Linux

```bash
# Добавьте пользователя в группу dialout
sudo usermod -a -G dialout $USER

# Перезайдите в систему
```

---

## 📊 Сравнение размеров

| Платформа | Размер | Примечания |
|-----------|--------|------------|
| Windows | ~50 MB | Включает Python runtime |
| Linux | ~45 MB | Включает Python runtime |
| macOS | ~55 MB | Включает Python runtime |

---

## 🔐 Подпись кода (опционально)

### Windows

Для подписи `.exe` используйте SignTool:
```powershell
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist\DVLINK_GUI\DVLINK_GUI.exe
```

### macOS

Для подписи `.app` используйте codesign:
```bash
codesign --deep --force --verify --verbose --sign "Developer ID" dist/DVLINK_GUI.app
```

---

## 📝 Чеклист перед релизом

- [ ] Все тесты пройдены
- [ ] Rust модуль скомпилирован
- [ ] Приложение запускается на Windows
- [ ] Приложение запускается на Linux
- [ ] COM порты определяются корректно
- [ ] USB мониторинг работает
- [ ] Файлы собраны в архивы
- [ ] Создан тег версии
- [ ] GitHub Actions собрал релиз

---

## 📞 Поддержка

При проблемах со сборкой:

1. Проверьте логи сборки
2. Убедитесь что все зависимости установлены
3. Попробуйте чистую сборку: `pyinstaller --clean ...`
4. Проверьте версии Python и Rust

---

**Последнее обновление:** Февраль 2026
**Версия документа:** 1.0
