"""
EXIF 信息查看对话框 - 主题跟随主窗口
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget, QWidget,
    QHeaderView, QTextEdit, QGroupBox,
)
from PyQt5.QtCore import Qt

from src.widgets.theme import ThemeTokens, build_dialog_stylesheet


class ExifDialog(QDialog):
    """EXIF 信息查看对话框，样式跟随主题。"""

    def __init__(self, exif_data: dict, image_info: dict, tokens: ThemeTokens, parent=None):
        super().__init__(parent)

        self.exif_data = exif_data or {}
        self.image_info = image_info or {}
        self._tokens = tokens

        self.setWindowTitle("EXIF 信息")
        self.setMinimumSize(600, 700)
        self.resize(700, 750)

        self.setStyleSheet(build_dialog_stylesheet(tokens))
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        title_label = QLabel("EXIF 信息")
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)

        if self.image_info:
            info_group = QGroupBox("基本信息")
            info_layout = QVBoxLayout(info_group)

            grid_widget = QWidget()
            grid_layout = QHBoxLayout(grid_widget)
            grid_layout.setSpacing(20)

            info_items = []
            if 'filename' in self.image_info:
                info_items.append(("文件名", self.image_info.get('filename', '-')))
            if 'dimensions' in self.image_info:
                w, h = self.image_info['dimensions']
                info_items.append(("尺寸", f"{w} x {h}"))
            if 'format' in self.image_info:
                info_items.append(("格式", self.image_info['format']))
            if 'file_size' in self.image_info:
                size = self.image_info['file_size']
                if size > 1024 * 1024:
                    size_str = f"{size / 1024 / 1024:.2f} MB"
                else:
                    size_str = f"{size / 1024:.2f} KB"
                info_items.append(("文件大小", size_str))
            if 'mode' in self.image_info:
                info_items.append(("色彩模式", self.image_info.get('mode', '-')))

            for label, value in info_items:
                card = QWidget()
                card_layout = QVBoxLayout(card)
                card_layout.setSpacing(4)

                label_widget = QLabel(label)
                label_widget.setObjectName("muted")
                card_layout.addWidget(label_widget)

                value_widget = QLabel(str(value))
                value_widget.setObjectName("valueLabel")
                card_layout.addWidget(value_widget)

                grid_layout.addWidget(card)

            grid_layout.addStretch()
            info_layout.addWidget(grid_widget)
            layout.addWidget(info_group)

        tab_widget = QTabWidget()
        tab_widget.setDocumentMode(True)

        basic_tab = self._create_basic_tab()
        tab_widget.addTab(basic_tab, "基本信息")

        camera_tab = self._create_camera_tab()
        tab_widget.addTab(camera_tab, "拍摄信息")

        gps_tab = self._create_gps_tab()
        tab_widget.addTab(gps_tab, "位置信息")

        raw_tab = self._create_raw_tab()
        tab_widget.addTab(raw_tab, "原始数据")

        layout.addWidget(tab_widget)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        copy_btn = QPushButton("复制全部 EXIF")
        copy_btn.setObjectName("secondaryBtn")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        btn_layout.addWidget(copy_btn)

        btn_layout.addSpacing(12)

        close_btn = QPushButton("关闭")
        close_btn.setObjectName("primary")
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(100)
        btn_layout.addWidget(close_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _create_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["属性", "值"])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        return table

    def _populate_table(self, table: QTableWidget, data: list) -> None:
        if not data:
            table.setRowCount(1)
            table.setItem(0, 0, QTableWidgetItem("提示"))
            table.setItem(0, 1, QTableWidgetItem("未读取到相关信息"))
        else:
            table.setRowCount(len(data))
            for i, (key, value) in enumerate(data):
                table.setItem(i, 0, QTableWidgetItem(key))
                table.setItem(i, 1, QTableWidgetItem(str(value)))

    def _create_basic_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)

        table = self._create_table()
        basic_info = []

        if 'DateTime' in self.exif_data:
            basic_info.append(("拍摄日期", self.exif_data['DateTime']))
        if 'DateTimeOriginal' in self.exif_data:
            basic_info.append(("原始日期", self.exif_data['DateTimeOriginal']))
        if 'DateTimeDigitized' in self.exif_data:
            basic_info.append(("数字化日期", self.exif_data['DateTimeDigitized']))
        if 'XResolution' in self.exif_data and 'YResolution' in self.exif_data:
            res = f"{self.exif_data['XResolution']} x {self.exif_data['YResolution']}"
            basic_info.append(("分辨率", res))
        if 'Software' in self.exif_data:
            basic_info.append(("软件", self.exif_data['Software']))
        if 'Copyright' in self.exif_data:
            basic_info.append(("版权", self.exif_data['Copyright']))
        if 'Artist' in self.exif_data:
            basic_info.append(("作者", self.exif_data['Artist']))
        if 'ImageDescription' in self.exif_data:
            basic_info.append(("图像描述", self.exif_data['ImageDescription']))

        self._populate_table(table, basic_info)
        layout.addWidget(table)
        return tab

    def _create_camera_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)

        table = self._create_table()
        camera_info = []

        if 'Make' in self.exif_data:
            camera_info.append(("相机品牌", self.exif_data['Make']))
        if 'Model' in self.exif_data:
            camera_info.append(("相机型号", self.exif_data['Model']))
        if 'LensModel' in self.exif_data:
            camera_info.append(("镜头型号", self.exif_data['LensModel']))
        if 'ISOSpeedRatings' in self.exif_data:
            camera_info.append(("ISO", str(self.exif_data['ISOSpeedRatings'])))
        if 'FNumber' in self.exif_data:
            camera_info.append(("光圈", f"f/{self.exif_data['FNumber']}"))
        if 'ExposureTime' in self.exif_data:
            time = self.exif_data['ExposureTime']
            if isinstance(time, tuple):
                camera_info.append(("快门速度", f"{time[0]}/{time[1]}s"))
            else:
                camera_info.append(("快门速度", f"{time}s"))
        if 'FocalLength' in self.exif_data:
            focal = self.exif_data['FocalLength']
            if isinstance(focal, tuple):
                camera_info.append(("焦距", f"{focal[0] / focal[1]:.1f}mm"))
            else:
                camera_info.append(("焦距", f"{focal}mm"))
        if 'ExposureBiasValue' in self.exif_data:
            camera_info.append(("曝光补偿", f"{self.exif_data['ExposureBiasValue']}EV"))
        if 'MeteringMode' in self.exif_data:
            camera_info.append(("测光模式", self.exif_data['MeteringMode']))
        if 'Flash' in self.exif_data:
            flash_str = "开启" if self.exif_data['Flash'] else "关闭"
            camera_info.append(("闪光灯", flash_str))
        if 'WhiteBalance' in self.exif_data:
            camera_info.append(("白平衡", self.exif_data['WhiteBalance']))
        if 'ExposureProgram' in self.exif_data:
            camera_info.append(("曝光程序", self.exif_data['ExposureProgram']))

        self._populate_table(table, camera_info)
        layout.addWidget(table)
        return tab

    def _create_gps_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)

        gps_info = []

        if 'GPSLatitude' in self.exif_data and 'GPSLatitudeRef' in self.exif_data:
            lat = self.exif_data['GPSLatitude']
            lat_ref = self.exif_data['GPSLatitudeRef']
            gps_info.append(("纬度", f"{lat[0]}deg {lat[1]}' {lat[2]}\" {lat_ref}"))
        if 'GPSLongitude' in self.exif_data and 'GPSLongitudeRef' in self.exif_data:
            lon = self.exif_data['GPSLongitude']
            lon_ref = self.exif_data['GPSLongitudeRef']
            gps_info.append(("经度", f"{lon[0]}deg {lon[1]}' {lon[2]}\" {lon_ref}"))
        if 'GPSAltitude' in self.exif_data:
            gps_info.append(("海拔", f"{self.exif_data['GPSAltitude']}m"))
        if 'GPSTimeStamp' in self.exif_data:
            ts = self.exif_data['GPSTimeStamp']
            gps_info.append(("GPS 时间", f"{ts[0]}:{ts[1]}:{ts[2]}"))
        if 'GPSDateStamp' in self.exif_data:
            gps_info.append(("GPS 日期", self.exif_data['GPSDateStamp']))

        if not gps_info:
            empty_label = QLabel("此图片不包含 GPS 位置信息")
            empty_label.setObjectName("muted")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setContentsMargins(40, 60, 40, 60)
            layout.addStretch()
            layout.addWidget(empty_label)
            layout.addStretch()
        else:
            table = self._create_table()
            self._populate_table(table, gps_info)
            layout.addWidget(table)

        return tab

    def _create_raw_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setLineWrapMode(QTextEdit.NoWrap)

        if self.exif_data:
            lines = []
            for key, value in sorted(self.exif_data.items()):
                if isinstance(value, bytes):
                    value_str = f"<bytes: {len(value)}>"
                else:
                    value_str = str(value)
                lines.append(f"{key:30s} = {value_str}")
            text_edit.setPlainText("\n".join(lines))
        else:
            text_edit.setPlainText("此图片没有 EXIF 信息")

        layout.addWidget(text_edit)
        return tab

    def _copy_to_clipboard(self):
        from PyQt5.QtWidgets import QApplication

        text = "EXIF 信息:\n\n"
        for key, value in sorted(self.exif_data.items()):
            text += f"{key}: {value}\n"

        QApplication.clipboard().setText(text)

        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "成功", "EXIF 信息已复制到剪贴板")
