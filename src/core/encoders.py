"""JPEG/PNG 编码器：优先 mozjpeg / oxipng，失败回退 Pillow。"""

import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Dict, Optional

from PIL import Image

from src.config import DEFAULT_COMPRESS_LEVEL_PNG, DEFAULT_WEBP_METHOD

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_TOOL_CACHE: Dict[str, Optional[str]] = {}
_TOOL_DISABLED = set()


def _platform_tools_dir() -> Optional[Path]:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "tools"

    root = Path(__file__).resolve().parent.parent.parent / "tools"
    machine = platform.machine().lower()
    if sys.platform == "darwin":
        folder = "macos-arm64" if machine in {"arm64", "aarch64"} else "macos-x64"
    elif sys.platform == "win32":
        folder = "windows-x64"
    else:
        folder = "linux-x64"
    candidate = root / folder
    return candidate if candidate.exists() else root


def _lookup_tool(name: str) -> Optional[str]:
    exe = f"{name}.exe" if sys.platform == "win32" else name
    tools_dir = _platform_tools_dir()
    candidates = []
    if tools_dir is not None:
        candidates.append(tools_dir / exe)
        candidates.append(tools_dir / name)
    which = shutil.which(name) or shutil.which(exe)
    if which:
        candidates.append(Path(which))
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def _find_tool(name: str) -> Optional[str]:
    with _LOCK:
        if name in _TOOL_DISABLED:
            return None
        if name not in _TOOL_CACHE:
            _TOOL_CACHE[name] = _lookup_tool(name)
        return _TOOL_CACHE[name]


def _disable_tool(name: str, reason: Exception) -> None:
    with _LOCK:
        _TOOL_DISABLED.add(name)
        _TOOL_CACHE[name] = None
    logger.warning("%s 不可用，后续改用内置编码器: %s", name, reason)


def _run_tool(args, timeout: int) -> None:
    subprocess.run(
        args,
        check=True,
        capture_output=True,
        timeout=timeout,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )


def save_jpeg(img: Image.Image, dst_path: Path, quality: int, keep_exif: bool = False) -> None:
    # 进程内 Pillow 可并行。外部 cjpeg 要先写整张 PPM 再排队，大批量会慢一个数量级。
    _save_jpeg_pillow(img, dst_path, quality, keep_exif)


def save_png(img: Image.Image, dst_path: Path) -> None:
    _save_png_pillow(img, dst_path)


def save_webp(img: Image.Image, dst_path: Path, quality: int, keep_exif: bool = False) -> None:
    save_kwargs = {
        "format": "WEBP",
        "quality": quality,
        "method": DEFAULT_WEBP_METHOD,
    }
    if keep_exif:
        exif = img.info.get("exif")
        if exif is not None:
            save_kwargs["exif"] = exif
    img.save(dst_path, **save_kwargs)


def _save_jpeg_pillow(img: Image.Image, dst_path: Path, quality: int, keep_exif: bool) -> None:
    save_kwargs = {
        "format": "JPEG",
        "quality": quality,
        "optimize": True,
        "progressive": True,
        "subsampling": 2,
    }
    if keep_exif:
        exif = img.info.get("exif")
        if exif is not None:
            save_kwargs["exif"] = exif
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save(dst_path, **save_kwargs)


def _save_jpeg_mozjpeg(img: Image.Image, dst_path: Path, quality: int, cjpeg: str) -> None:
    fd, tmp_name = tempfile.mkstemp(suffix=".ppm")
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        img.save(tmp_path, format="PPM")
        _run_tool(
            [
                cjpeg,
                "-quality",
                str(int(quality)),
                "-progressive",
                "-optimize",
                "-outfile",
                str(dst_path),
                str(tmp_path),
            ],
            timeout=120,
        )
    finally:
        tmp_path.unlink(missing_ok=True)


def _save_png_pillow(img: Image.Image, dst_path: Path) -> None:
    img.save(
        dst_path,
        format="PNG",
        optimize=True,
        compress_level=DEFAULT_COMPRESS_LEVEL_PNG,
    )
