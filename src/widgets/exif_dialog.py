"""
EXIF 信息查看对话框 - 现代深色玻璃拟态风格
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget, QWidget,
    QHeaderView, QTextEdit, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class ExifDialog(QDialog):
    """EXIF 信息查看对话框 - 现代风格"""
    
    def __init__(self, exif_data: dict, image_info: dict, parent=None):
        super().__init__(parent)
        
        self.exif_data = exif_data or {}
        self.image_info = image_info or {}
        
        self.setWindowTitle("EXIF 信息")
        self.setMinimumSize(600, 700)
        self.resize(700, 750)
        
        # 应用样式
        self.setStyleSheet("""
            QDialog {
                background-color: #0d0d12;
            }
            
            QGroupBox {
                background-color: rgba(30, 30, 40, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
                margin-top: 12px;
                padding: 20px;
                font-weight: 600;
            }
            
            QGroupBox::title {
                color: #a29bfe;
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            QLabel {
                color: #e8e8ed;
            }
            
            QLabel#titleLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 700;
            }
            
            QLabel#valueLabel {
                color: #a29bfe;
                font-weight: 500;
            }
            
            QTableWidget {
                background-color: rgba(30, 30, 40, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                gridline-color: rgba(255, 255, 255, 0.05);
                selection-background-color: rgba(108, 92, 231, 0.3);
                selection-color: #ffffff;
            }
            
            QTableWidget::item {
                padding: 10px;
                color: #e8e8ed;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
            
            QTableWidget::item:selected {
                background-color: rgba(108, 92, 231, 0.3);
            }
            
            QHeaderView::section {
                background: rgba(30, 30, 40, 0.8);
                color: #a29bfe;
                padding: 12px;
                border: none;
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            QHeaderView::section:first {
                border-top-left-radius: 12px;
            }
            
            QHeaderView::section:last {
                border-top-right-radius: 12px;
            }
            
            QTextEdit {
                background-color: rgba(20, 20, 28, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 16px;
                color: #e8e8ed;
                font-family: 'JetBrains Mono', monospace;
                font-size: 12px;
                line-height: 1.6;
            }
            
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6c5ce7, stop:1 #a29bfe);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 12px 24px;
                font-weight: 600;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7d6cf0, stop:1 #b3acff);
            }
            
            QPushButton#secondaryBtn {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
            }
            
            QPushButton#secondaryBtn:hover {
                background: rgba(255, 255, 255, 0.12);
            }
            
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            
            QTabBar::tab {
                background-color: rgba(255, 255, 255, 0.05);
                color: #8b8b9b;
                padding: 10px 20px;
                margin-right: 8px;
                border-radius: 10px;
                border: none;
            }
            
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(108, 92, 231, 0.3), stop:1 rgba(162, 155, 254, 0.3));
                color: #ffffff;
                border: 1px solid rgba(162, 155, 254, 0.3);
            }
        """)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # ========== 标题 ==========
        title_label = QLabel("📷 EXIF 信息")
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)
        
        # ========== 基本信息卡片 ==========
        if self.image_info:
            info_group = QGroupBox("📊 基本信息")
            info_layout = QVBoxLayout(info_group)
            
            # 信息网格
            grid_widget = QWidget()
            grid_layout = QHBoxLayout(grid_widget)
            grid_layout.setSpacing(20)
            
            info_items = []
            
            # 文件名
            if 'filename' in self.image_info:
                info_items.append(("文件名", self.image_info.get('filename', '-')))
            
            # 尺寸
            if 'dimensions' in self.image_info:
                w, h = self.image_info['dimensions']
                info_items.append(("尺寸", f"{w} × {h}"))
            
            # 格式
            if 'format' in self.image_info:
                fmt = self.image_info['format']
                info_items.append(("格式", fmt))
            
            # 文件大小
            if 'file_size' in self.image_info:
                size = self.image_info['file_size']
                if size > 1024 * 1024:
                    size_str = f"{size / 1024 / 1024:.2f} MB"
                else:
                    size_str = f"{size / 1024:.2f} KB"
                info_items.append(("文件大小", size_str))
            
            # 模式
            if 'mode' in self.image_info:
                info_items.append(("色彩模式", self.image_info.get('mode', '-')))
            
            # 创建信息卡片
            for label, value in info_items:
                card = QWidget()
                card_layout = QVBoxLayout(card)
                card_layout.setSpacing(4)
                
                label_widget = QLabel(label)
                label_widget.setStyleSheet("color: #8b8b9b; font-size: 11px;")
                card_layout.addWidget(label_widget)
                
                value_widget = QLabel(str(value))
                value_widget.setObjectName("valueLabel")
                card_layout.addWidget(value_widget)
                
                grid_layout.addWidget(card)
            
            grid_layout.addStretch()
            info_layout.addWidget(grid_widget)
            layout.addWidget(info_group)
        
        # ========== 标签页 ==========
        tab_widget = QTabWidget()
        tab_widget.setDocumentMode(True)
        
        # --- 基本信息页 ---
        basic_tab = self._create_basic_tab()
        tab_widget.addTab(basic_tab, "📋 基本信息")
        
        # --- 拍摄信息页 ---
        camera_tab = self._create_camera_tab()
        tab_widget.addTab(camera_tab, "📸 拍摄信息")
        
        # --- GPS 信息页 ---
        gps_tab = self._create_gps_tab()
        tab_widget.addTab(gps_tab, "🌍 位置信息")
        
        # --- 完整 EXIF 页 ---
        raw_tab = self._create_raw_tab()
        tab_widget.addTab(raw_tab, "📝 原始数据")
        
        layout.addWidget(tab_widget)
        
        # ========== 底部按钮 ==========
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        copy_btn = QPushButton("📋 复制")
        copy_btn.setObjectName("secondaryBtn")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        btn_layout.addWidget(copy_btn)
        
        btn_layout.addSpacing(12)
        
        close_btn = QPushButton("关闭")
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(100)
        btn_layout.addWidget(close_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _create_basic_tab(self):
        """创建基本信息标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)
        
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["属性", "值"])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        
        # 基本 EXIF 信息
        basic_info = []
        
        # 日期时间
        if 'DateTime' in self.exif_data:
            basic_info.append(("拍摄日期", self.exif_data['DateTime']))
        if 'DateTimeOriginal' in self.exif_data:
            basic_info.append(("原始日期", self.exif_data['DateTimeOriginal']))
        if 'DateTimeDigitized' in self.exif_data:
            basic_info.append(("数字化日期", self.exif_data['DateTimeDigitized']))
        
        # 分辨率
        if 'XResolution' in self.exif_data and 'YResolution' in self.exif_data:
            res = f"{self.exif_data['XResolution']} × {self.exif_data['YResolution']}"
            basic_info.append(("分辨率", res))
        
        # 软件
        if 'Software' in self.exif_data:
            basic_info.append(("软件", self.exif_data['Software']))
        
        # 版权
        if 'Copyright' in self.exif_data:
            basic_info.append(("版权", self.exif_data['Copyright']))
        
        # 作者
        if 'Artist' in self.exif_data:
            basic_info.append(("作者", self.exif_data['Artist']))
        
        # 图像描述
        if 'ImageDescription' in self.exif_data:
            basic_info.append(("图像描述", self.exif_data['ImageDescription']))
        
        table.setRowCount(len(basic_info))
        for i, (key, value) in enumerate(basic_info):
            table.setItem(i, 0, QTableWidgetItem(key))
            table.setItem(i, 1, QTableWidgetItem(str(value)))
        
        layout.addWidget(table)
        return tab
    
    def _create_camera_tab(self):
        """创建拍摄信息标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)
        
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["属性", "值"])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        
        # 相机信息
        camera_info = []
        
        # 相机品牌
        if 'Make' in self.exif_data:
            camera_info.append(("相机品牌", self.exif_data['Make']))
        
        # 相机型号
        if 'Model' in self.exif_data:
            camera_info.append(("相机型号", self.exif_data['Model']))
        
        # 镜头信息
        if 'LensModel' in self.exif_data:
            camera_info.append(("镜头型号", self.exif_data['LensModel']))
        
        # ISO
        if 'ISOSpeedRatings' in self.exif_data:
            camera_info.append(("ISO", str(self.exif_data['ISOSpeedRatings'])))
        
        # 光圈
        if 'FNumber' in self.exif_data:
            camera_info.append(("光圈", f"f/{self.exif_data['FNumber']}"))
        
        # 快门速度
        if 'ExposureTime' in self.exif_data:
            time = self.exif_data['ExposureTime']
            if isinstance(time, tuple):
                camera_info.append(("快门速度", f"{time[0]}/{time[1]}s"))
            else:
                camera_info.append(("快门速度", f"{time}s"))
        
        # 焦距
        if 'FocalLength' in self.exif_data:
            focal = self.exif_data['FocalLength']
            if isinstance(focal, tuple):
                camera_info.append(("焦距", f"{focal[0] / focal[1]:.1f}mm"))
            else:
                camera_info.append(("焦距", f"{focal}mm"))
        
        # 曝光补偿
        if 'ExposureBiasValue' in self.exif_data:
            bias = self.exif_data['ExposureBiasValue']
            camera_info.append(("曝光补偿", f"{bias}EV"))
        
        # 测光模式
        if 'MeteringMode' in self.exif_data:
            camera_info.append(("测光模式", self.exif_data['MeteringMode']))
        
        # 闪光灯
        if 'Flash' in self.exif_data:
            flash = self.exif_data['Flash']
            flash_str = "开启" if flash else "关闭"
            camera_info.append(("闪光灯", flash_str))
        
        # 白平衡
        if 'WhiteBalance' in self.exif_data:
            camera_info.append(("白平衡", self.exif_data['WhiteBalance']))
        
        # 曝光程序
        if 'ExposureProgram' in self.exif_data:
            camera_info.append(("曝光程序", self.exif_data['ExposureProgram']))
        
        table.setRowCount(len(camera_info))
        for i, (key, value) in enumerate(camera_info):
            table.setItem(i, 0, QTableWidgetItem(key))
            table.setItem(i, 1, QTableWidgetItem(str(value)))
        
        layout.addWidget(table)
        return tab
    
    def _create_gps_tab(self):
        """创建 GPS 信息标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)
        
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["属性", "值"])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        
        # GPS 信息
        gps_info = []
        
        # 纬度
        if 'GPSLatitude' in self.exif_data and 'GPSLatitudeRef' in self.exif_data:
            lat = self.exif_data['GPSLatitude']
            lat_ref = self.exif_data['GPSLatitudeRef']
            lat_str = f"{lat[0]}° {lat[1]}' {lat[2]}\" {lat_ref}"
            gps_info.append(("纬度", lat_str))
        
        # 经度
        if 'GPSLongitude' in self.exif_data and 'GPSLongitudeRef' in self.exif_data:
            lon = self.exif_data['GPSLongitude']
            lon_ref = self.exif_data['GPSLongitudeRef']
            lon_str = f"{lon[0]}° {lon[1]}' {lon[2]}\" {lon_ref}"
            gps_info.append(("经度", lon_str))
        
        # 海拔
        if 'GPSAltitude' in self.exif_data:
            alt = self.exif_data['GPSAltitude']
            gps_info.append(("海拔", f"{alt}m"))
        
        # 时间戳
        if 'GPSTimeStamp' in self.exif_data:
            ts = self.exif_data['GPSTimeStamp']
            time_str = f"{ts[0]}:{ts[1]}:{ts[2]}"
            gps_info.append(("GPS 时间", time_str))
        
        # 日期戳
        if 'GPSDateStamp' in self.exif_data:
            gps_info.append(("GPS 日期", self.exif_data['GPSDateStamp']))
        
        if not gps_info:
            no_gps_label = QLabel("🚫 此图片不包含 GPS 信息")
            no_gps_label.setAlignment(Qt.AlignCenter)
            no_gps_label.setStyleSheet("color: #8b8b9b; font-size: 14px; padding: 40px;")
            layout.addWidget(no_gps_label)
        else:
            table.setRowCount(len(gps_info))
            for i, (key, value) in enumerate(gps_info):
                table.setItem(i, 0, QTableWidgetItem(key))
                table.setItem(i, 1, QTableWidgetItem(str(value)))
            layout.addWidget(table)
        
        return tab
    
    def _create_raw_tab(self):
        """创建原始 EXIF 数据标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setLineWrapMode(QTextEdit.NoWrap)
        
        # 构建原始数据文本
        if self.exif_data:
            lines = []
            for key, value in sorted(self.exif_data.items()):
                # 格式化值
                if isinstance(value, bytes):
                    value_str = f"<bytes: {len(value)}>"
                elif isinstance(value, tuple):
                    value_str = str(value)
                else:
                    value_str = str(value)
                lines.append(f"{key:30s} = {value_str}")
            text_edit.setPlainText("\n".join(lines))
        else:
            text_edit.setPlainText("此图片没有 EXIF 信息")
        
        layout.addWidget(text_edit)
        return tab
    
    def _copy_to_clipboard(self):
        """复制 EXIF 数据到剪贴板"""
        from PyQt5.QtWidgets import QApplication
        
        text = f"EXIF 信息:\n\n"
        for key, value in sorted(self.exif_data.items()):
            text += f"{key}: {value}\n"
        
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        
        # 显示提示
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "成功", "EXIF 信息已复制到剪贴板")
