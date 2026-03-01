"""
工作线程模块 - 处理批量压缩任务
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Dict, Any

from PyQt5.QtCore import QObject, pyqtSignal

from src.config import IMAGE_EXTENSIONS, MAX_WORKERS, DYNAMIC_THREADING, config_manager
from src.core.compressor import compress_image


class WorkerSignals(QObject):
    """工作线程信号定义"""
    progress = pyqtSignal(int, str)  # 进度百分比, 消息
    file_completed = pyqtSignal(dict)  # 单个文件完成信息
    result = pyqtSignal(dict)        # 结果字典
    finished = pyqtSignal()          # 完成信号


class CompressWorker(QObject):
    """
    图片压缩工作线程
    
    使用线程池并行处理多张图片的压缩任务
    支持动态线程控制和详细统计
    """
    
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self._is_canceled = False
        self._executor: Optional[ThreadPoolExecutor] = None
        self._overwrite = False
        self.detailed_stats: List[Dict[str, Any]] = []
    
    def cancel(self) -> None:
        """取消压缩任务"""
        self._is_canceled = True
    
    def calculate_optimal_workers(self, files: List[Path]) -> int:
        """
        计算最优线程数
        
        根据文件大小动态调整：
        - 大文件（>5MB）：减少线程数，避免内存溢出
        - 小文件（<500KB）：增加线程数，提高吞吐量
        """
        if not DYNAMIC_THREADING or not files:
            return MAX_WORKERS or os.cpu_count() or 4
        
        cpu_count = os.cpu_count() or 4
        total_size = sum(f.stat().st_size for f in files if f.exists())
        avg_size = total_size / len(files) if files else 0
        
        # 根据平均文件大小调整线程数
        if avg_size > 10 * 1024 * 1024:  # > 10MB
            return max(2, cpu_count // 2)
        elif avg_size > 5 * 1024 * 1024:  # > 5MB
            return max(2, cpu_count - 1)
        elif avg_size < 100 * 1024:  # < 100KB
            return min(cpu_count * 2, 16)
        else:
            return cpu_count
    
    def run(
        self,
        input_dir: str,
        output_dir: str,
        quality: int,
        include_subdirs: bool,
        min_size_mb: float,
        overwrite: bool = False,
        max_width: int = 0,
        max_height: int = 0,
        keep_ratio: bool = True,
        output_format: str = "original",
        smart_mode: bool = False,
        target_size_kb: int = 0,
        rename_pattern: Optional[str] = None,
        keep_exif: bool = True,
        auto_rotate: bool = True,
    ) -> None:
        """
        执行批量压缩任务
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            quality: 压缩质量 (1-100)
            include_subdirs: 是否包含子目录
            min_size_mb: 最小文件大小 (MB)
            overwrite: 是否覆盖原文件
            max_width: 最大宽度（0 表示不限制）
            max_height: 最大高度（0 表示不限制）
            keep_ratio: 是否保持比例
            output_format: 输出格式
            smart_mode: 是否启用智能压缩
            target_size_kb: 智能压缩目标大小（KB）
            rename_pattern: 重命名模式
            keep_exif: 是否保留 EXIF 信息
            auto_rotate: 是否根据 EXIF 方向自动旋转
            max_width: 最大宽度（0 表示不限制）
            max_height: 最大高度（0 表示不限制）
            keep_ratio: 是否保持比例
            output_format: 输出格式
            smart_mode: 是否启用智能压缩
            target_size_kb: 智能压缩目标大小（KB）
            rename_pattern: 重命名模式
        """
        self._is_canceled = False
        self.detailed_stats = []
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        min_size_bytes = int(min_size_mb * 1024 * 1024)
        
        # 生成设置哈希（用于增量压缩）
        settings_dict = {
            "quality": quality,
            "max_width": max_width,
            "max_height": max_height,
            "output_format": output_format,
            "smart_mode": smart_mode,
            "target_size_kb": target_size_kb,
        }
        settings_hash = str(settings_dict)
        
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
        processed = skipped = too_small = failed = cached = 0
        total_orig = total_comp = 0
        
        # 计算最优线程数
        optimal_workers = self.calculate_optimal_workers(all_files)
        self.signals.progress.emit(0, f"检测到 {total} 个文件，使用 {optimal_workers} 个线程...")
        
        with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
            self._executor = executor
            
            future_to_file = {
                executor.submit(
                    compress_image,
                    f,
                    input_path,
                    output_path,
                    quality,
                    min_size_bytes,
                    overwrite,
                    max_width,
                    max_height,
                    keep_ratio,
                    output_format,
                    smart_mode,
                    target_size_kb,
                    rename_pattern,
                    i,
                    settings_hash,
                    keep_exif,
                    auto_rotate,
                ): (f, i)
                for i, f in enumerate(all_files)
            }
            
            for i, future in enumerate(as_completed(future_to_file)):
                if self._is_canceled:
                    break
                
                file_path, file_index = future_to_file[future]
                src_path, status, orig_sz, new_sz, details = future.result()
                
                # 记录详细统计
                stat_record = {
                    "index": file_index + 1,
                    "filename": src_path.name,
                    "status": status,
                    "original_size": orig_sz,
                    "compressed_size": new_sz,
                    **details,
                }
                self.detailed_stats.append(stat_record)
                self.signals.file_completed.emit(stat_record)
                
                if status == "processed":
                    processed += 1
                    total_orig += orig_sz
                    total_comp += new_sz
                elif status == "skipped":
                    skipped += 1
                elif status == "too_small":
                    too_small += 1
                elif status == "cached":
                    cached += 1
                    total_orig += orig_sz
                    total_comp += new_sz
                else:
                    failed += 1
                
                msg = f"[{i+1}/{total}] {status}: {src_path.name}"
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
                "cached": cached,
                "total_orig": total_orig,
                "total_comp": total_comp,
                "saved": saved,
                "avg_ratio": avg_ratio,
                "detailed_stats": self.detailed_stats,
                "thread_count": optimal_workers,
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
