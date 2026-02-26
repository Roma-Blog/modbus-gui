# -*- mode: python ; coding: utf-8 -*-

# Добавляем скрытые импорты для PyQt5 и других модулей
hidden_imports = [
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.QtNetwork',
    'PyQt5.QtPrintSupport',
    'serial',
    'serial.tools.list_ports',
    'modbus_worker',
    'modbus_connection',
    'modbus_device_info',
    'modbus_registers',
    'modbus_rtu_client',
    'modbus_rtu_scanner',
    'device_response_parser_fixed',
    'json',
    'datetime',
    'typing',
    'sys',
    'os'
]

a = Analysis(
    ['modbus_gui_main.py'],
    pathex=['../'],  # Добавляем путь к корню проекта
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='modbus_gui_main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='modbus_gui_main'
)
