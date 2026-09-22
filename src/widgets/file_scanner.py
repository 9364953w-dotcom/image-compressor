"""后台扫描控制器，避免在 UI 线程 rglob。"""

import threading
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSignal

from src.core.scanner import collect_images


class FileScanController(QObject):
    """在后台线程扫描目录，通过信号回传结果。"""

    finished = pyqtSignal(int, object)

    def start(self, root: str, include_subdirs: bool, generation: int) -> None:
        def work() -> None:
            try:
                files = collect_images(Path(root), include_subdirs)
            except Exception:
                files = []
            self.finished.emit(generation, files)

        thread = threading.Thread(target=work, daemon=True, name=f"scan-{generation}")
        thread.start()
