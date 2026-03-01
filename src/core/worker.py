"""
工作线程模块 - 处理批量压缩任务
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

from PyQt5.QtCore import QObject, pyqtSignal

from src.config import IMAGE_EXTENSIONS, MAX_WORKERS
from src.core.compressor import compress_image


class WorkerSignals(QObject):
    """工作线程信号定义"""
    progress = pyqtSignal(int, str)  # 进度百分比, 消息
    result = pyqtSignal(dict)        # 结果字典
    finished = pyqtSignal()          # 完成信号


class CompressWorker(QObject):
    """
    图片压缩工作线程
    
    使用线程池并行处理多张图片的压缩任务
    """
    
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self._is_canceled = False
        self._executor: Optional[ThreadPoolExecutor] = None
    
    def cancel(self) -> None:
        """取消压缩任务"""
        self._is_canceled = True
    
    def run(
        self,
        input_dir: str,
        output_dir: str,
        quality: int,
        include_subdirs: bool,
        min_size_mb: float,
        overwrite: bool = False,
    ) -> None:
        """
        执行批量压缩任务
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            quality: 压缩质量 (1-100)
            include_subdirs: 是否包含子目录
            min_size_mb: 最小文件大小 (MB)
        """
        self._is_canceled = False
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        min_size_bytes = int(min_size_mb * 1024 * 1024)
        self._overwrite = overwrite
        
        # 收集图片文件
        all_files = self._collect_images(input_path, include_subdirs)
        
        if not all_files:
            self.signals.result.emit({"error": "No images found!"})
            self.signals.finished.emit()
            return
        
        # 创建输出目录
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 统计初始化
        total = len(all_files)
        processed = skipped = too_small = failed = 0
        total_orig = total_comp = 0
        
        # 使用线程池并行处理
        max_workers = MAX_WORKERS or os.cpu_count()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            self._executor = executor
            
            future_to_file = {
                executor.submit(
                    compress_image,
                    f,
                    input_path,
                    output_path,
                    quality,
                    min_size_bytes,
                    self._overwrite,
                ): f
                for f in all_files
            }
            
            for i, future in enumerate(as_completed(future_to_file)):
                if self._is_canceled:
                    break
                
                file_path, status, orig_sz, new_sz = future.result()
                
                if status == "processed":
                    processed += 1
                    total_orig += orig_sz
                    total_comp += new_sz
                elif status == "skipped":
                    skipped += 1
                elif status == "too_small":
                    too_small += 1
                else:
                    failed += 1
                
                msg = f"Processed: {file_path.name}"
                self.signals.progress.emit(int((i + 1) / total * 100), msg)
        
        self._executor = None
        
        # 发送结果
        if self._is_canceled:
            self.signals.result.emit({"canceled": True})
        else:
            saved = total_orig - total_comp
            avg_ratio = (total_comp / total_orig * 100) if total_orig > 0 else 0
            self.signals.result.emit({
                "processed": processed,
                "skipped": skipped,
                "too_small": too_small,
                "failed": failed,
                "total_orig": total_orig,
                "total_comp": total_comp,
                "saved": saved,
                "avg_ratio": avg_ratio,
            })
        
        self.signals.finished.emit()
    
    def _collect_images(self, input_path: Path, include_subdirs: bool) -> List[Path]:
        """
        收集所有图片文件
        
        Args:
            input_path: 输入目录
            include_subdirs: 是否包含子目录
            
        Returns:
            图片文件路径列表
        """
        if include_subdirs:
            return [
                p for p in input_path.rglob('*')
                if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
            ]
        else:
            return [
                p for p in input_path.iterdir()
                if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
            ]
