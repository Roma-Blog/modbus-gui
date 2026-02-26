#!/bin/bash
# Скрипт сборки DVLINK GUI для Linux
# Использование: ./build_linux.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================"
echo "DVLINK GUI - Сборка для Linux"
echo "========================================"

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден!"
    exit 1
fi
echo "✓ Python: $(python3 --version)"

# Проверка виртуального окружения
if [ ! -d ".venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Установка зависимостей
echo "Установка зависимостей..."
pip install --upgrade pip
pip install pyserial PyQt5 pyinstaller pyudev

# Проверка Rust
if ! command -v rustc &> /dev/null; then
    echo "❌ Rust не найден!"
    echo "Установите: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi
echo "✓ Rust: $(rustc --version)"

# Проверка Maturin
if ! command -v maturin &> /dev/null; then
    echo "Установка Maturin..."
    pip install maturin
fi
echo "✓ Maturin: $(maturin --version)"

# Сборка Rust модуля
echo "Сборка Rust модуля..."
cd modbus_scanner_rust
maturin develop --release
cd ..

# Проверка Rust модуля
echo "Проверка Rust модуля..."
python -c "import modbus_scanner_rust; print('✓ Rust модуль: OK')"

# Сборка PyInstaller
echo "Сборка приложения..."
pyinstaller --clean modbus_gui_wizard.spec

# Проверка результата
if [ -d "dist/DVLINK_GUI" ]; then
    echo ""
    echo "========================================"
    echo "✅ Сборка завершена успешно!"
    echo "========================================"
    echo ""
    echo "Приложение в: dist/DVLINK_GUI/"
    echo ""
    echo "Для запуска:"
    echo "  cd dist/DVLINK_GUI"
    echo "  ./DVLINK_GUI"
    echo ""
    
    # Создание tar.gz архива
    echo "Создание архива..."
    cd dist
    tar -czf DVLINK_GUI_Linux.tar.gz DVLINK_GUI/
    cd ..
    echo "Архив: dist/DVLINK_GUI_Linux.tar.gz"
    echo ""
else
    echo "❌ Ошибка сборки!"
    exit 1
fi
