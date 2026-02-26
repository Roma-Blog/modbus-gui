# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec для сборки DVLINK GUI Wizard (кроссплатформенно)

Использование:
    pyinstaller --clean modbus_gui_wizard.spec

Требования:
    - Python 3.8+
    - Rust toolchain (для modbus_scanner_rust)
    - pip install pyinstaller pyserial PyQt5
"""

import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Путь к проекту (используем cwd для совместимости с GitHub Actions)
project_dir = os.getcwd()

# Определение платформы
IS_WINDOWS = sys.platform.startswith('win')
IS_LINUX = sys.platform.startswith('linux')
IS_MACOS = sys.platform.startswith('darwin')

# Скрытые импорты для PyQt5 и других модулей
hidden_imports = [
    # PyQt5
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.QtNetwork',
    'PyQt5.QtPrintSupport',
    
    # Serial
    'serial',
    'serial.tools',
    'serial.tools.list_ports',
    
    # Модули проекта
    'wizard',
    'wizard.wizard_main',
    'wizard.step_welcome',
    'wizard.step_connect',
    'wizard.step_config',
    'wizard.connection_monitor',
    'wizard.usb_monitor',
    'wizard.config_worker',
    'wizard.components',
    'wizard.components.log_viewer',
    'wizard.components.connection_status',
    'core',
    'core.modbus_connection',
    'core.modbus_device_info',
    'core.modbus_registers',
    'core.modbus_rtu_client',
    'core.device_response_parser_fixed',
    'auto_search_worker',
    'modbus_worker',
    'modbus_scanner_wrapper',
    'config_manager',
    'constants',
    'firmware_display',
    'gui_environment',
    
    # Стандартные
    'json',
    'datetime',
    'typing',
    'threading',
    'queue',
    'ctypes',
    'logging',
    'platform',
    # Кроссплатформенные импорты serial
    'serial.tools.list_ports.posix',
    'serial.tools.list_ports.windows',
    'serial.tools.list_ports.macos',
]

# Данные проекта (JSON конфиги, и т.д.)
datas = [
    (os.path.join(project_dir, 'modbus_gui_settings.json'), '.'),
]

# Проверяем наличие core/config.json
core_config = os.path.join(project_dir, 'core', 'config.json')
if os.path.exists(core_config):
    datas.append((core_config, 'core'))

# Rust библиотека (нужно скомпилировать отдельно!)
# Ищем в корневой директории и в modbus_scanner_rust/
rust_lib_names = ['modbus_scanner_rust']
rust_found = False

for lib_name in rust_lib_names:
    # Поиск в корневой директории
    for ext in ['.pyd', '.so', '.dll']:
        lib_path = os.path.join(project_dir, f'{lib_name}{ext}')
        if os.path.exists(lib_path):
            datas.append((lib_path, '.'))
            rust_found = True
            print(f"[SPEC] Found Rust library: {lib_path}")
            break
    
    # Поиск в поддиректориях
    if not rust_found:
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                if file.startswith(lib_name) and (file.endswith('.pyd') or file.endswith('.so')):
                    lib_path = os.path.join(root, file)
                    datas.append((lib_path, '.'))
                    rust_found = True
                    print(f"[SPEC] Found Rust library: {lib_path}")
                    break
            if rust_found:
                break

if not rust_found:
    print("[SPEC] WARNING: Rust library not found! Application may not work.")
    print("[SPEC] Run: cd modbus_scanner_rust && maturin develop --release")

# Иконка (опционально)
icon_file = None
for ext in ['.ico', '.png', '.icns']:
    potential_icon = os.path.join(project_dir, f'icon{ext}')
    if os.path.exists(potential_icon):
        icon_file = potential_icon
        print(f"[SPEC] Using icon: {icon_file}")
        break

# Бинарные файлы (библиотеки)
binaries = []

# Для Windows: добавляем VCRUNTIME если есть
if IS_WINDOWS:
    try:
        import ctypes.util
        # PyInstaller обычно сам находит необходимые библиотеки
    except:
        pass

# Для Linux: добавляем libudev если есть
if IS_LINUX:
    # Проверяем наличие libudev
    import subprocess
    try:
        result = subprocess.run(['ldconfig', '-p'], capture_output=True, text=True)
        if 'libudev.so' in result.stdout:
            print("[SPEC] libudev found - will be included automatically")
    except:
        pass

a = Analysis(
    [os.path.join(project_dir, '__main__.py')],
    pathex=[project_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'tkinter',
        'IPython',
        'jupyter',
        'pytest',
        'nose',
        'unittest',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DVLINK_GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,  # GUI приложение (без консоли)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DVLINK_GUI',
)
