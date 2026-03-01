"""
图片压缩核心逻辑模块
"""

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Tuple, Literal

from PIL import Image, ImageFile

from src.config import (
    DEFAULT_COMPRESS_LEVEL_PNG,
    DEFAULT_WEBP_METHOD,
    IMAGE_EXTENSIONS,
)

# 解除 Pillow 图像尺寸限制
Image.MAX_IMAGE_PIXELS = None
# 确保加载所有图像插件
ImageFile.LOAD_TRUNCATED_IMAGES = True

logger = logging.getLogger(__name__)

# 状态类型定义
CompressStatus = Literal["processed", "skipped", "too_small", "failed"]


def compress_image(
    src_path: Path,
    input_root: Path,
    output_root: Path,
    quality: int,
    min_size_bytes: int,
    overwrite: bool = False,
) -> Tuple[Path, CompressStatus, int, int]:
    """
    压缩单张图片
    
    Args:
        src_path: 源图片路径
        input_root: 输入根目录
        output_root: 输出根目录
        quality: 压缩质量 (1-100)
        min_size_bytes: 最小文件大小（小于此值的文件跳过）
        overwrite: 是否直接覆盖原文件
        
    Returns:
        Tuple[源路径, 状态, 原始大小, 新大小]
    """
    orig_size = 0
    
    try:
        # 获取原始文件大小
        orig_size = src_path.stat().st_size
        
        # 检查文件大小
        if orig_size <= min_size_bytes:
            return src_path, "too_small", orig_size, 0
        
        # 计算目标路径
        if overwrite:
            # 覆盖模式：原路径即为目标路径
            dst_path = src_path
        else:
            dst_path = output_root / src_path.relative_to(input_root)
        
        # 检查文件是否已存在（非覆盖模式下跳过）
        if not overwrite and dst_path.exists():
            return src_path, "skipped", orig_size, dst_path.stat().st_size
        
        # 覆盖模式下使用临时文件
        temp_path = None
        actual_save_path = dst_path
        if overwrite:
            # 创建临时文件
            temp_fd, temp_path_str = tempfile.mkstemp(
                suffix=src_path.suffix,
                dir=src_path.parent,
                prefix=f".{src_path.stem}_temp_"
            )
            os.close(temp_fd)
            temp_path = Path(temp_path_str)
            actual_save_path = temp_path
        else:
            # 创建目标目录
            dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 处理图片
        with Image.open(src_path) as img:
            # 转换模式，保留 PNG 透明度
            suffix = src_path.suffix.lower()
            
            if suffix == '.png':
                # PNG 保持 RGBA 模式以保留透明度
                if img.mode not in ("RGBA", "RGB", "P"):
                    img = img.convert("RGBA")
            elif img.mode in ("RGBA", "P"):
                # 其他格式转 RGB（无透明度需求）
                img = img.convert("RGB")
            elif img.mode == "CMYK":
                img = img.convert("RGB")
            
            # 根据格式保存
            if suffix in ('.jpg', '.jpeg'):
                _save_jpeg(img, actual_save_path, quality)
            elif suffix == '.png':
                _save_png(img, actual_save_path)
            elif suffix == '.webp':
                _save_webp(img, actual_save_path, quality)
            else:
                # 其他格式使用默认保存
                img.save(actual_save_path)
        
        # 覆盖模式下替换原文件
        if overwrite and temp_path:
            # 原子性替换：先备份原文件（可选），然后替换
            backup_path = src_path.with_suffix(f"{src_path.suffix}.backup")
            try:
                # 创建原文件备份（压缩成功后删除）
                shutil.copy2(src_path, backup_path)
                # 替换原文件
                shutil.move(str(temp_path), str(src_path))
                # 删除备份
                backup_path.unlink(missing_ok=True)
            except Exception as e:
                # 恢复备份
                if backup_path.exists():
                    shutil.move(str(backup_path), str(src_path))
                raise e
        
        new_size = dst_path.stat().st_size
        return src_path, "processed", orig_size, new_size
        
    except Exception as e:
        logger.error(f"处理失败 {src_path}: {e}", exc_info=True)
        return src_path, "failed", orig_size, 0


def _save_jpeg(img: Image.Image, dst_path: Path, quality: int) -> None:
    """保存为 JPEG 格式，保留 EXIF"""
    exif = img.info.get('exif')
    save_kwargs = {
        "format": "JPEG",
        "quality": quality,
        "optimize": True,
    }
    if exif is not None:
        save_kwargs["exif"] = exif
    
    # 确保是 RGB 模式
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    img.save(dst_path, **save_kwargs)


def _save_png(img: Image.Image, dst_path: Path) -> None:
    """保存为 PNG 格式，使用优化压缩"""
    save_kwargs = {
        "format": "PNG",
        "optimize": True,
        "compress_level": DEFAULT_COMPRESS_LEVEL_PNG,
    }
    img.save(dst_path, **save_kwargs)


def _save_webp(img: Image.Image, dst_path: Path, quality: int) -> None:
    """保存为 WebP 格式，保留 EXIF"""
    exif = img.info.get('exif')
    save_kwargs = {
        "format": "WEBP",
        "quality": quality,
        "method": DEFAULT_WEBP_METHOD,
    }
    if exif is not None:
        save_kwargs["exif"] = exif
    
    img.save(dst_path, **save_kwargs)
