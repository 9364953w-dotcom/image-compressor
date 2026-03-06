"""
工作线程模块 - 处理批量压缩任务
"""

import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import QObject, pyqtSignal

from src.config import DYNAMIC_THREADING, IMAGE_EXTENSIONS, MAX_WORKERS
from src.core.compressor import compress_image


class CompressWorker(QObject):
    """图片压缩工作线程（统一事件契约 + 状态机）"""

    state_changed = pyqtSignal(str, dict)
    progress = pyqtSignal(dict)
    file_completed = pyqtSignal(dict)
    result = pyqtSignal(dict)
    finished = pyqtSignal(dict)

    def __init__(
        self,
        *,
        input_dir: str,
        output_dir: Optional[str],
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
        incremental: bool = True,
        max_retries: int = 1,
        backup_set: Optional[Path] = None,
    ):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.quality = quality
        self.include_subdirs = include_subdirs
        self.min_size_mb = min_size_mb
        self.overwrite = overwrite
        self.max_width = max_width
        self.max_height = max_height
        self.keep_ratio = keep_ratio
        self.output_format = output_format
        self.smart_mode = smart_mode
        self.target_size_kb = target_size_kb
        self.rename_pattern = rename_pattern
        self.keep_exif = keep_exif
        self.auto_rotate = auto_rotate
        self.incremental = incremental
        self.max_retries = max_retries
        self.backup_set = backup_set

        self._is_canceled = False
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._executor: Optional[ThreadPoolExecutor] = None

    def cancel(self) -> None:
        self._is_canceled = True
        self._pause_event.set()
        self.state_changed.emit("Canceling", {})

    def pause(self) -> None:
        self._pause_event.clear()
        self.state_changed.emit("Paused", {})

    def resume(self) -> None:
        self._pause_event.set()
        self.state_changed.emit("Running", {})

    @property
    def is_paused(self) -> bool:
        return not self._pause_event.is_set()

    def calculate_optimal_workers(self, files: List[Path]) -> int:
        if not DYNAMIC_THREADING or not files:
            return MAX_WORKERS or os.cpu_count() or 4

        cpu_count = os.cpu_count() or 4
        total_size = sum(f.stat().st_size for f in files if f.exists())
        avg_size = total_size / len(files) if files else 0

        if avg_size > 10 * 1024 * 1024:
            return max(2, cpu_count // 2)
        if avg_size > 5 * 1024 * 1024:
            return max(2, cpu_count - 1)
        if avg_size < 100 * 1024:
            return min(cpu_count * 2, 16)
        return cpu_count

    def _compress_with_retry(self, *args, **kwargs):
        last_exc = None
        for attempt in range(self.max_retries + 1):
            try:
                return compress_image(*args, **kwargs), attempt
            except Exception as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    time.sleep(0.5)
        raise last_exc

    def run(self) -> None:
        start_ts = time.time()
        self.state_changed.emit("Validating", {})

        input_path = Path(self.input_dir)
        if not input_path.exists() or not input_path.is_dir():
            payload = {"error": "输入目录不存在或无效", "state": "Error"}
            self.result.emit(payload)
            self.finished.emit(payload)
            return

        if self.overwrite or not self.output_dir:
            output_path = input_path
        else:
            output_path = Path(self.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

        min_size_bytes = int(self.min_size_mb * 1024 * 1024)
        settings_hash = str(
            {
                "quality": self.quality,
                "max_width": self.max_width,
                "max_height": self.max_height,
                "output_format": self.output_format,
                "smart_mode": self.smart_mode,
                "target_size_kb": self.target_size_kb,
                "incremental": self.incremental,
            }
        )

        self.state_changed.emit("Scanning", {})
        all_files = self._collect_images(input_path, self.include_subdirs)
        total = len(all_files)
        if total == 0:
            payload = {"error": "未找到可处理图片", "state": "Error"}
            self.result.emit(payload)
            self.finished.emit(payload)
            return

        worker_count = self.calculate_optimal_workers(all_files)
        self.state_changed.emit("Running", {"total": total, "workers": worker_count})

        detailed_stats: List[Dict[str, Any]] = []
        status_counter = {"processed": 0, "skipped": 0, "too_small": 0, "failed": 0, "cached": 0}
        total_orig = 0
        total_comp = 0

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            self._executor = executor
            future_to_meta = {
                executor.submit(
                    self._compress_with_retry,
                    file_path,
                    input_path,
                    output_path,
                    self.quality,
                    min_size_bytes,
                    self.overwrite,
                    self.max_width,
                    self.max_height,
                    self.keep_ratio,
                    self.output_format,
                    self.smart_mode,
                    self.target_size_kb,
                    self.rename_pattern,
                    index,
                    settings_hash if self.incremental else None,
                    self.keep_exif,
                    self.auto_rotate,
                    self.backup_set,
                ): (index, file_path)
                for index, file_path in enumerate(all_files)
            }

            completed = 0
            for future in as_completed(future_to_meta):
                self._pause_event.wait()
                if self._is_canceled:
                    break

                index, _ = future_to_meta[future]
                try:
                    (src_path, status, orig_size, new_size, details), retry_count = future.result()
                except Exception:
                    src_path = _
                    status = "failed"
                    orig_size = 0
                    new_size = 0
                    details = {}
                    retry_count = self.max_retries

                status_counter[status] = status_counter.get(status, 0) + 1

                if status in {"processed", "cached"}:
                    total_orig += orig_size
                    total_comp += new_size

                record = {
                    "index": index + 1,
                    "path": str(src_path),
                    "filename": src_path.name if hasattr(src_path, "name") else str(src_path),
                    "status": status,
                    "original_size": orig_size,
                    "compressed_size": new_size,
                    "details": details,
                    "retry_count": retry_count,
                }
                detailed_stats.append(record)
                self.file_completed.emit(record)

                completed += 1
                elapsed = max(0.001, time.time() - start_ts)
                rate = completed / elapsed
                remaining = total - completed
                eta_seconds = remaining / rate if rate > 0 else 0.0

                self.progress.emit(
                    {
                        "current": completed,
                        "total": total,
                        "percent": int(completed / total * 100),
                        "message": f"[{completed}/{total}] {status}: {src_path.name if hasattr(src_path, 'name') else src_path}",
                        "rate": rate,
                        "eta_seconds": eta_seconds,
                    }
                )

        self._executor = None
        self.state_changed.emit("Finalizing", {})

        saved = total_orig - total_comp
        avg_ratio = (total_comp / total_orig * 100) if total_orig > 0 else 0
        canceled = self._is_canceled
        payload = {
            "state": "Cancelled" if canceled else "Done",
            "canceled": canceled,
            "processed": status_counter.get("processed", 0),
            "skipped": status_counter.get("skipped", 0),
            "too_small": status_counter.get("too_small", 0),
            "failed": status_counter.get("failed", 0),
            "cached": status_counter.get("cached", 0),
            "total_orig": total_orig,
            "total_comp": total_comp,
            "saved": saved,
            "avg_ratio": avg_ratio,
            "detailed_stats": sorted(detailed_stats, key=lambda x: x["index"]),
            "thread_count": worker_count,
            "elapsed_seconds": time.time() - start_ts,
            "total_files": total,
        }

        if canceled:
            self.state_changed.emit("Cancelled", payload)
        else:
            self.state_changed.emit("Done", payload)
        self.result.emit(payload)
        self.finished.emit(payload)

    def _collect_images(self, input_path: Path, include_subdirs: bool) -> List[Path]:
        if include_subdirs:
            files = [p for p in input_path.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
        else:
            files = [p for p in input_path.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
        return sorted(files)
