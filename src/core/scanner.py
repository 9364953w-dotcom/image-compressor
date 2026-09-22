"""目录扫描：收集可压缩图片。"""

from pathlib import Path
from typing import List

from src.config import IMAGE_EXTENSIONS


def collect_images(root: Path, include_subdirs: bool = True) -> List[Path]:
    """扫描目录中的图片文件，按路径排序。"""
    if not root.exists() or not root.is_dir():
        return []
    if include_subdirs:
        files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    else:
        files = [p for p in root.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    return sorted(files)
