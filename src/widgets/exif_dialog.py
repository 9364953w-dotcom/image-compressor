"""
EXIF 信息查看对话框
"""

from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QTextEdit, QSplitter, QWidget
)
from PyQt5.QtCore import Qt

from src.core.compressor import get_exif_info


class ExifDialog(QDialog):
    """EXIF 信息查看对话框"""
    
    def __init__(self, image_path: Path, parent=None):
        super().__init__(parent)
        
        self.image_path = image_path
        self.setWindowTitle(f"EXIF 信息 - {image_path.name}")
        self.setMinimumSize(600, 500)
        self.resize(700, 600)
        
        self._setup_ui()
        self._load_exif()
    
    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # 文件信息
        info_widget = QWidget()
        info_layout = QHBoxLayout(info_widget)
        info_layout.setSpacing(20)
        
        self.filename_label = QLabel(f"<b>文件名:</b> {self.image_path.name}")
        info_layout.addWidget(self.filename_label)
        
        self.size_label = QLabel(f"<b>大小:</b> -")
        info_layout.addWidget(self.size_label)
        
        info_layout.addStretch()
        
        layout.addWidget(info_widget)
        
        # 分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 基本信息组
        basic_group = QGroupBox("📷 基本信息")
        basic_layout = QVBoxLayout(basic_group)
        
        self.basic_table = QTableWidget()
        self.basic_table.setColumnCount(2)
        self.basic_table.setHorizontalHeaderLabels(["项目", "值"])
        self.basic_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.basic_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.basic_table.setAlternatingRowColors(True)
        basic_layout.addWidget(self.basic_table)
        
        splitter.addWidget(basic_group)
        
        # 原始 EXIF 数据组
        raw_group = QGroupBox("📋 完整 EXIF 数据")
        raw_layout = QVBoxLayout(raw_group)
        
        self.raw_text = QTextEdit()
        self.raw_text.setReadOnly(True)
        self.raw_text.setPlaceholderText("加载中...")
        raw_layout.addWidget(self.raw_text)
        
        splitter.addWidget(raw_group)
        
        splitter.setSizes([250, 350])
        layout.addWidget(splitter)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        ok_btn = QPushButton("确定")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setFixedWidth(80)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_exif(self):
        """加载 EXIF 信息"""
        # 获取文件大小
        try:
            size = self.image_path.stat().st_size
            from src.utils import format_bytes
            self.size_label.setText(f"<b>大小:</b> {format_bytes(size)}")
        except Exception:
            pass
        
        # 获取 EXIF 信息
        exif_info = get_exif_info(self.image_path)
        
        if not exif_info["has_exif"]:
            self.basic_table.setRowCount(1)
            self.basic_table.setItem(0, 0, QTableWidgetItem("状态"))
            self.basic_table.setItem(0, 1, QTableWidgetItem("此图片没有 EXIF 信息"))
            self.raw_text.setPlainText("此图片没有 EXIF 信息")
            return
        
        # 填充基本信息表
        basic_data = [
            ("相机", exif_info.get("camera") or "未知"),
            ("拍摄日期", exif_info.get("date") or "未知"),
            ("原始尺寸", exif_info.get("size") or "未知"),
            ("GPS 信息", exif_info.get("gps") or "无"),
            ("方向", str(exif_info.get("orientation", "1"))),
        ]
        
        self.basic_table.setRowCount(len(basic_data))
        for i, (key, value) in enumerate(basic_data):
            self.basic_table.setItem(i, 0, QTableWidgetItem(key))
            self.basic_table.setItem(i, 1, QTableWidgetItem(value))
        
        # 填充原始 EXIF 数据
        raw_data = exif_info.get("raw", {})
        if raw_data:
            text_lines = []
            for tag, value in sorted(raw_data.items()):
                text_lines.append(f"{tag}: {value}")
            self.raw_text.setPlainText("\n".join(text_lines))
        else:
            self.raw_text.setPlainText("无法读取详细 EXIF 数据")
