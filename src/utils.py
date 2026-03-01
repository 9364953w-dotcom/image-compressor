"""
工具函数模块
"""

import logging
from pathlib import Path

from src.config import LOG_FILE, LOG_LEVEL, LOG_FORMAT


def setup_logging() -> logging.Logger:
    """配置并返回日志记录器"""
    logging.basicConfig(
        filename=LOG_FILE,
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        encoding='utf-8'
    )
    return logging.getLogger(__name__)


def format_bytes(bytes_val: int) -> str:
    """
    将字节数格式化为人类可读的字符串
    
    Args:
        bytes_val: 字节数
        
    Returns:
        格式化后的字符串，如 "1.5 MB"
    """
    if bytes_val < 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} TB"


def get_resource_path(filename: str) -> Path:
    """
    获取资源文件的绝对路径
    
    Args:
        filename: 资源文件名
        
    Returns:
        资源的绝对路径
    """
    from src.config import RESOURCES_DIR
    return RESOURCES_DIR / filename
