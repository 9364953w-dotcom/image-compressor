# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件

打包命令:
    pyinstaller 图片压缩工具.spec

生成位置:
    dist/图片压缩工具.app (macOS)
    dist/图片压缩工具 (Windows/Linux 单文件)
"""

import platform
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(SPECPATH)
SRC_DIR = PROJECT_ROOT / "src"


def _collect_tool_binaries():
    machine = platform.machine().lower()
    if sys.platform == "darwin":
        folder = "macos-arm64" if machine in {"arm64", "aarch64"} else "macos-x64"
    elif sys.platform == "win32":
        folder = "windows-x64"
    else:
        folder = "linux-x64"
    tools_dir = PROJECT_ROOT / "tools" / folder
    binaries = []
    if not tools_dir.exists():
        return binaries
    for name in ("cjpeg", "cjpeg.exe", "oxipng", "oxipng.exe", "libjpeg.62.dylib", "libpng16.16.dylib"):
        path = tools_dir / name
        if path.exists():
            binaries.append((str(path), "tools"))
    return binaries


TOOL_BINARIES = _collect_tool_binaries()
UPX_EXCLUDE = [Path(src).name for src, _dest in TOOL_BINARIES]

# 分析模块
a = Analysis(
    ['src/__main__.py'],
    pathex=[str(SRC_DIR)],
    binaries=TOOL_BINARIES,
    datas=[
        # 包含资源文件
        (str(SRC_DIR / "resources" / "icon.icns"), "src/resources"),
        (str(SRC_DIR / "resources" / "menu_icon.png"), "src/resources"),
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'pillow_heif',
        'src.config',
        'src.utils',
        'src.core',
        'src.core.compressor',
        'src.core.worker',
        'src.core.encoders',
        'src.core.scanner',
        'src.widgets',
        'src.widgets.drag_drop',
        'src.widgets.main_window',
        'src.widgets.splash_screen',
        'src.widgets.tray_controller',
        'src.widgets.drop_sensor',
        'src.widgets.drop_shelf',
        'src.widgets.file_scanner',
        'src.widgets.drag_proximity',
        'src.widgets.window_level',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不必要的模块以减小体积
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'tkinter',
        'unittest',
        'pydoc',
        'email',
        'http',
        'xml',
        'html',
        'lib2to3',
        'distutils',
    ],
    noarchive=False,
    optimize=2,  # 启用字节码优化
)

pyz = PYZ(a.pure)

# macOS App Bundle 配置
if sys.platform == 'darwin':
    # macOS 使用 .app 包格式
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='图片压缩工具',
        debug=False,
        bootloader_ignore_signals=False,
        strip=True,
        upx=True,
        upx_exclude=UPX_EXCLUDE,
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=str(SRC_DIR / "resources" / "icon.icns"),
    )
    
    app = BUNDLE(
        exe,
        name='图片压缩工具.app',
        icon=str(SRC_DIR / "resources" / "icon.icns"),
        bundle_identifier='com.wang.imagecompressor',
        version='1.6.0',
        info_string='图片批量压缩工具',
    )
else:
    # Windows/Linux 单文件可执行程序
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='图片压缩工具',
        debug=False,
        bootloader_ignore_signals=False,
        strip=True,
        upx=True,
        upx_exclude=UPX_EXCLUDE,
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=str(SRC_DIR / "resources" / "icon.icns") if sys.platform != 'win32' else str(SRC_DIR / "resources" / "icon.png"),
    )
