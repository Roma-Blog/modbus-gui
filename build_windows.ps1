# DVLINK GUI - Сборка для Windows
# Использование: .\build_windows.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================"
Write-Host "DVLINK GUI - Сборка для Windows"
Write-Host "========================================"

# Проверка Python
Write-Host "Проверка Python..."
try {
    $pythonVersion = python --version
    Write-Host "✓ Python: $pythonVersion"
} catch {
    Write-Host "❌ Python не найден!"
    Write-Host "Установите Python 3.8+ с https://python.org"
    exit 1
}

# Проверка виртуального окружения
if (-not (Test-Path ".venv")) {
    Write-Host "Создание виртуального окружения..."
    python -m venv .venv
}

& ".venv\Scripts\Activate.ps1"

# Установка зависимостей
Write-Host "Установка зависимостей..."
pip install --upgrade pip
pip install pyserial PyQt5 pyinstaller

# Проверка Rust
Write-Host "Проверка Rust..."
try {
    $rustVersion = rustc --version
    Write-Host "✓ Rust: $rustVersion"
} catch {
    Write-Host "❌ Rust не найден!"
    Write-Host "Установите: winget install Rustlang.Rust.MSVC"
    exit 1
}

# Проверка Maturin
Write-Host "Проверка Maturin..."
try {
    $maturinVersion = maturin --version
    Write-Host "✓ Maturin: $maturinVersion"
} catch {
    Write-Host "Установка Maturin..."
    pip install maturin
}

# Сборка Rust модуля
Write-Host "Сборка Rust модуля..."
Set-Location modbus_scanner_rust
maturin develop --release
Set-Location ..

# Проверка Rust модуля
Write-Host "Проверка Rust модуля..."
python -c "import modbus_scanner_rust; print('OK')"

# Сборка PyInstaller
Write-Host "Сборка приложения..."
pyinstaller --clean modbus_gui_wizard.spec

# Проверка результата
if (Test-Path "dist\DVLINK_GUI") {
    Write-Host ""
    Write-Host "========================================"
    Write-Host "✅ Сборка завершена успешно!"
    Write-Host "========================================"
    Write-Host ""
    Write-Host "Приложение в: dist\DVLINK_GUI\"
    Write-Host ""
    Write-Host "Для запуска:"
    Write-Host "  cd dist\DVLINK_GUI"
    Write-Host "  .\DVLINK_GUI.exe"
    Write-Host ""
    
    # Создание ZIP архива
    Write-Host "Создание ZIP архива..."
    Set-Location dist
    Compress-Archive -Path DVLINK_GUI -DestinationPath DVLINK_GUI_Windows.zip -Force
    Set-Location ..
    Write-Host "Архив: dist\DVLINK_GUI_Windows.zip"
    Write-Host ""
} else {
    Write-Host "❌ Ошибка сборки!"
    exit 1
}
