"""
图片压缩核心逻辑模块
"""

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Tuple, Literal, Optional, Dict, Any

from PIL import Image, ImageFile

from src.config import (
    DEFAULT_COMPRESS_LEVEL_PNG,
    DEFAULT_WEBP_METHOD,
    IMAGE_EXTENSIONS,
    config_manager,
)

# 解除 Pillow 图像尺寸限制
Image.MAX_IMAGE_PIXELS = None
# 确保加载所有图像插件
ImageFile.LOAD_TRUNCATED_IMAGES = True

logger = logging.getLogger(__name__)

# 状态类型定义
CompressStatus = Literal["processed", "skipped", "too_small", "failed", "cached"]


def calculate_new_size(
    img: Image.Image,
    max_width: int,
    max_height: int,
    keep_ratio: bool = True
) -> Tuple[int, int]:
    """
    计算调整后尺寸
    
    Args:
        img: 原图
        max_width: 最大宽度（0 表示不限制）
        max_height: 最大高度（0 表示不限制）
        keep_ratio: 是否保持比例
        
    Returns:
        (新宽度, 新高度)
    """
    orig_width, orig_height = img.size
    
    # 如果都不限制，返回原尺寸
    if max_width <= 0 and max_height <= 0:
        return orig_width, orig_height
    
    new_width, new_height = orig_width, orig_height
    
    if keep_ratio:
        # 计算缩放比例
        ratio = 1.0
        
        if max_width > 0 and orig_width > max_width:
            ratio = min(ratio, max_width / orig_width)
        
        if max_height > 0 and orig_height > max_height:
            ratio = min(ratio, max_height / orig_height)
        
        new_width = int(orig_width * ratio)
        new_height = int(orig_height * ratio)
    else:
        # 不保持比例，直接调整到指定大小
        if max_width > 0:
            new_width = max_width
        if max_height > 0:
            new_height = max_height
    
    # 确保至少为 1
    new_width = max(1, new_width)
    new_height = max(1, new_height)
    
    return new_width, new_height


def smart_compress(
    img: Image.Image,
    dst_path: Path,
    target_size_kb: int,
    tolerance: float = 0.1,
    output_format: str = "jpg",
) -> Tuple[bool, int]:
    """
    智能压缩 - 自动寻找最佳质量参数
    
    Args:
        img: 图片对象
        dst_path: 目标路径
        target_size_kb: 目标大小（KB）
        tolerance: 容差比例
        output_format: 输出格式
        
    Returns:
        (是否成功, 最终文件大小)
    """
    target_bytes = target_size_kb * 1024
    min_quality, max_quality = 10, 95
    best_quality = 85
    best_size = float('inf')
    best_temp_path = None
    
    # 二分查找最佳质量
    temp_dir = tempfile.mkdtemp()
    
    try:
        for _ in range(6):  # 最多6次尝试
            quality = (min_quality + max_quality) // 2
            
            temp_path = Path(temp_dir) / f"test_{quality}.tmp"
            
            # 保存测试
            if output_format in ('jpg', 'jpeg'):
                _save_jpeg(img, temp_path, quality)
            elif output_format == 'webp':
                _save_webp(img, temp_path, quality)
            else:
                break
            
            size = temp_path.stat().st_size
            
            # 如果在容差范围内，直接返回
            if abs(size - target_bytes) / target_bytes <= tolerance:
                best_quality = quality
                best_size = size
                best_temp_path = temp_path
                break
            
            # 记录最佳结果
            if abs(size - target_bytes) < abs(best_size - target_bytes):
                best_quality = quality
                best_size = size
                best_temp_path = temp_path
            
            # 调整质量范围
            if size > target_bytes:
                max_quality = quality - 1
            else:
                min_quality = quality + 1
        
        # 使用最佳结果
        if best_temp_path and best_temp_path.exists():
            shutil.copy2(best_temp_path, dst_path)
            return True, best_size
        
        return False, 0
        
    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True)


def get_exif_info(src_path: Path) -> Dict[str, Any]:
    """
    获取图片的 EXIF 信息
    
    Args:
        src_path: 图片路径
        
    Returns:
        EXIF 信息字典
    """
    info = {
        "has_exif": False,
        "camera": "",
        "date": "",
        "size": "",
        "gps": "",
        "orientation": 0,
        "raw": {},
    }
    
    try:
        from PIL.ExifTags import TAGS, GPSTAGS
        
        with Image.open(src_path) as img:
            exif = img._getexif()
            if not exif:
                return info
            
            info["has_exif"] = True
            info["raw"] = {TAGS.get(tag, tag): str(value) for tag, value in exif.items()}
            
            # 相机信息
            make = exif.get(0x010f, "")
            model = exif.get(0x0110, "")
            if make or model:
                info["camera"] = f"{make} {model}".strip()
            
            # 拍摄日期
            date_str = exif.get(0x9003, "") or exif.get(0x0132, "")
            if date_str:
                info["date"] = str(date_str)
            
            # 图片尺寸
            width = exif.get(0xA002, 0)
            height = exif.get(0xA003, 0)
            if width and height:
                info["size"] = f"{width}x{height}"
            
            # GPS 信息
            gps_info = exif.get(0x8825)
            if gps_info:
                info["gps"] = "有 GPS 信息"
            
            # 方向
            info["orientation"] = exif.get(0x0112, 1)
            
    except Exception as e:
        logger.debug(f"读取 EXIF 失败 {src_path}: {e}")
    
    return info


def compress_image(
    src_path: Path,
    input_root: Path,
    output_root: Path,
    quality: int,
    min_size_bytes: int,
    overwrite: bool = False,
    max_width: int = 0,
    max_height: int = 0,
    keep_ratio: bool = True,
    output_format: str = "original",
    smart_mode: bool = False,
    target_size_kb: int = 0,
    rename_pattern: Optional[str] = None,
    file_index: int = 0,
    settings_hash: Optional[str] = None,
    keep_exif: bool = True,
    auto_rotate: bool = True,
) -> Tuple[Path, CompressStatus, int, int, Dict[str, Any]]:
    """
    压缩单张图片
    
    Args:
        src_path: 源图片路径
        input_root: 输入根目录
        output_root: 输出根目录
        quality: 压缩质量 (1-100)
        min_size_bytes: 最小文件大小
        overwrite: 是否直接覆盖原文件
        max_width: 最大宽度（0 表示不限制）
        max_height: 最大高度（0 表示不限制）
        keep_ratio: 是否保持比例
        output_format: 输出格式（original/jpg/png/webp）
        smart_mode: 是否启用智能压缩
        target_size_kb: 智能压缩目标大小（KB）
        rename_pattern: 重命名模式
        file_index: 文件序号（用于重命名）
        settings_hash: 设置哈希（用于增量压缩）
        keep_exif: 是否保留 EXIF 信息
        auto_rotate: 是否根据 EXIF 方向自动旋转
        
    Returns:
        Tuple[源路径, 状态, 原始大小, 新大小, 详细信息]
    """
    orig_size = 0
    details = {
        "original_size": 0,
        "compressed_size": 0,
        "savings_percent": 0,
        "dimensions_before": "",
        "dimensions_after": "",
        "format_before": "",
        "format_after": "",
        "quality_used": quality,
        "resized": False,
        "renamed": False,
        "new_name": "",
        "exif_kept": keep_exif,
        "rotated": False,
    }
    
    try:
        # 获取原始文件大小
        orig_size = src_path.stat().st_size
        details["original_size"] = orig_size
        
        # 检查文件大小
        if orig_size <= min_size_bytes:
            return src_path, "too_small", orig_size, 0, details
        
        # 检查增量压缩缓存
        if settings_hash and config_manager.is_file_processed(src_path, settings_hash):
            return src_path, "cached", orig_size, orig_size, details
        
        # 确定输出格式
        suffix = src_path.suffix.lower()
        details["format_before"] = suffix
        
        if output_format == "original":
            output_ext = suffix
        else:
            output_ext = f".{output_format}"
        
        details["format_after"] = output_ext
        
        # 确定输出路径
        if overwrite:
            dst_path = src_path
        else:
            rel_path = src_path.relative_to(input_root)
            # 应用重命名模式
            if rename_pattern and rename_pattern != "{name}":
                from datetime import datetime
                name_without_ext = src_path.stem
                new_name = rename_pattern.format(
                    name=name_without_ext,
                    index=file_index + 1,
                    prefix="",
                    date=datetime.now().strftime("%Y%m%d"),
                )
                rel_path = rel_path.parent / f"{new_name}{output_ext}"
                details["renamed"] = True
                details["new_name"] = new_name
            else:
                # 只改扩展名
                if output_ext != suffix:
                    rel_path = rel_path.with_suffix(output_ext)
            
            dst_path = output_root / rel_path
        
        # 检查文件是否已存在（非覆盖模式下跳过）
        if not overwrite and dst_path.exists():
            existing_size = dst_path.stat().st_size
            return src_path, "skipped", orig_size, existing_size, details
        
        # 创建目标目录
        if not overwrite:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 覆盖模式下使用临时文件
        temp_path = None
        actual_save_path = dst_path
        if overwrite:
            temp_fd, temp_path_str = tempfile.mkstemp(
                suffix=src_path.suffix,
                dir=src_path.parent,
                prefix=f".{src_path.stem}_temp_"
            )
            os.close(temp_fd)
            temp_path = Path(temp_path_str)
            actual_save_path = temp_path
        
        # 处理图片
        with Image.open(src_path) as img:
            # 记录原始尺寸
            orig_width, orig_height = img.size
            details["dimensions_before"] = f"{orig_width}x{orig_height}"
            
            # 根据 EXIF 方向自动旋转
            if auto_rotate:
                try:
                    from PIL import ExifTags
                    orientation = None
                    for tag, value in img._getexif().items():
                        if ExifTags.TAGS.get(tag) == 'Orientation':
                            orientation = value
                            break
                    
                    if orientation:
                        rotate_map = {
                            3: Image.ROTATE_180,
                            6: Image.ROTATE_270,
                            8: Image.ROTATE_90,
                        }
                        if orientation in rotate_map:
                            img = img.transpose(rotate_map[orientation])
                            details["rotated"] = True
                            # 旋转后交换宽高
                            if orientation in [6, 8]:
                                orig_width, orig_height = orig_height, orig_width
                                details["dimensions_before"] = f"{orig_width}x{orig_height}"
                except Exception:
                    pass
            
            # 调整尺寸
            new_width, new_height = calculate_new_size(img, max_width, max_height, keep_ratio)
            if (new_width, new_height) != (orig_width, orig_height):
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                details["resized"] = True
                details["dimensions_after"] = f"{new_width}x{new_height}"
            else:
                details["dimensions_after"] = details["dimensions_before"]
            
            # 转换模式
            actual_format = output_ext.lstrip('.').lower()
            if actual_format == 'jpg':
                actual_format = 'jpeg'
            
            if actual_format == 'png':
                if img.mode not in ("RGBA", "RGB", "P", "L"):
                    img = img.convert("RGBA")
            elif img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            elif img.mode == "CMYK":
                img = img.convert("RGB")
            
            # 保存图片
            if smart_mode and target_size_kb > 0 and actual_format in ('jpeg', 'webp'):
                # 智能压缩模式
                success, new_size = smart_compress(
                    img, actual_save_path, target_size_kb, 
                    output_format=actual_format
                )
                if not success:
                    # 智能压缩失败，使用普通压缩
                    if actual_format == 'jpeg':
                        _save_jpeg(img, actual_save_path, quality, keep_exif)
                    else:
                        _save_webp(img, actual_save_path, quality, keep_exif)
            else:
                # 普通压缩模式
                if actual_format in ('jpg', 'jpeg'):
                    _save_jpeg(img, actual_save_path, quality, keep_exif)
                    details["quality_used"] = quality
                elif actual_format == 'png':
                    _save_png(img, actual_save_path)
                elif actual_format == 'webp':
                    _save_webp(img, actual_save_path, quality, keep_exif)
                    details["quality_used"] = quality
                else:
                    img.save(actual_save_path)
        
        # 覆盖模式下替换原文件
        if overwrite and temp_path:
            backup_path = src_path.with_suffix(f"{src_path.suffix}.backup")
            try:
                shutil.copy2(src_path, backup_path)
                shutil.move(str(temp_path), str(src_path))
                backup_path.unlink(missing_ok=True)
            except Exception as e:
                if backup_path.exists():
                    shutil.move(str(backup_path), str(src_path))
                raise e
        
        new_size = dst_path.stat().st_size
        details["compressed_size"] = new_size
        
        # 计算节省比例
        if orig_size > 0:
            details["savings_percent"] = ((orig_size - new_size) / orig_size) * 100
        
        # 更新缓存
        if settings_hash:
            config_manager.mark_file_processed(
                src_path, settings_hash,
                {"size": new_size, "path": str(dst_path)}
            )
        
        return src_path, "processed", orig_size, new_size, details
        
    except Exception as e:
        logger.error(f"处理失败 {src_path}: {e}", exc_info=True)
        # 清理临时文件
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)
        return src_path, "failed", orig_size, 0, details


def _save_jpeg(img: Image.Image, dst_path: Path, quality: int, keep_exif: bool = True) -> None:
    """保存为 JPEG 格式"""
    save_kwargs = {
        "format": "JPEG",
        "quality": quality,
        "optimize": True,
    }
    
    if keep_exif:
        exif = img.info.get('exif')
        if exif is not None:
            save_kwargs["exif"] = exif
    
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


def _save_webp(img: Image.Image, dst_path: Path, quality: int, keep_exif: bool = True) -> None:
    """保存为 WebP 格式"""
    save_kwargs = {
        "format": "WEBP",
        "quality": quality,
        "method": DEFAULT_WEBP_METHOD,
    }
    
    if keep_exif:
        exif = img.info.get('exif')
        if exif is not None:
            save_kwargs["exif"] = exif
    
    img.save(dst_path, **save_kwargs)
