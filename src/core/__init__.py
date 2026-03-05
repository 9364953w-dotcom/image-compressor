"""
核心功能模块
"""

from src.core.compressor import compress_image
from src.core.worker import CompressWorker

__all__ = ['compress_image', 'CompressWorker']
