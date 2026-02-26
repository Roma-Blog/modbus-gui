#!/bin/bash
# Скрипт запуска DVLINK GUI

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Сбрасываем snap-переменные (если VS Code из snap)
unset LD_LIBRARY_PATH
unset SNAP
unset SNAP_LIBRARY_PATH

# Активируем venv
source .venv/bin/activate

# Запускаем приложение с выбором интерфейса
python3 __main__.py "$@"
