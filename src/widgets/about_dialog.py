"""
关于对话框 - 现代深色玻璃拟态风格
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QTextEdit, QGroupBox, QFrame
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QFont

from src.config import APP_NAME, __version__


class AboutDialog(QDialog):
    """关于对话框 - 现代风格"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("关于")
        self.setMinimumSize(550, 650)
        self.resize(600, 700)
        
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
            
            QTextEdit {
                background-color: rgba(20, 20, 28, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 12px;
                color: #e8e8ed;
                font-family: 'JetBrains Mono', monospace;
                font-size: 12px;
            }
            
            QLabel {
                color: #e8e8ed;
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
        
        # ========== 软件标识区 ==========
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(8)
        
        # 软件名称
        name_label = QLabel(APP_NAME)
        name_font = QFont()
        name_font.setPointSize(28)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: #ffffff;")
        name_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(name_label)
        
        # 版本号
        version_label = QLabel(f"版本 {__version__}")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #a29bfe; font-size: 14px; font-weight: 600;")
        header_layout.addWidget(version_label)
        
        # 描述
        desc_label = QLabel("智能高效的图片批量处理工具")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #6b6b7b; font-size: 13px;")
        header_layout.addWidget(desc_label)
        
        layout.addWidget(header)
        
        # ========== 标签页 ==========
        tab_widget = QTabWidget()
        tab_widget.setDocumentMode(True)
        
        # --- 信息页 ---
        info_tab = self._create_info_tab()
        tab_widget.addTab(info_tab, "ℹ️ 信息")
        
        # --- 技术栈页 ---
        tech_tab = self._create_tech_tab()
        tab_widget.addTab(tech_tab, "🛠️ 技术栈")
        
        # --- 致谢页 ---
        thanks_tab = self._create_thanks_tab()
        tab_widget.addTab(thanks_tab, "🙏 致谢")
        
        layout.addWidget(tab_widget)
        
        # ========== 底部按钮 ==========
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        github_btn = QPushButton("🌐 GitHub")
        github_btn.setObjectName("secondaryBtn")
        github_btn.clicked.connect(self._open_github)
        btn_layout.addWidget(github_btn)
        
        btn_layout.addSpacing(12)
        
        ok_btn = QPushButton("确定")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setFixedWidth(100)
        btn_layout.addWidget(ok_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _create_info_tab(self):
        """创建信息标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignTop)
        
        # 开发者信息组
        dev_group = QGroupBox("👤 开发者信息")
        dev_layout = QVBoxLayout(dev_group)
        
        dev_info = QLabel(
            f"<b style='color: #a29bfe;'>开发者:</b> MWang<br>"
            f"<b style='color: #a29bfe;'>邮箱:</b> <a href='mailto:9364953@qq.com' style='color: #6c5ce7;'>9364953@qq.com</a><br>"
            f"<b style='color: #a29bfe;'>GitHub:</b> <a href='https://github.com/9364953w-dotcom' style='color: #6c5ce7;'>@9364953w-dotcom</a>"
        )
        dev_info.setOpenExternalLinks(True)
        dev_info.setTextInteractionFlags(Qt.TextBrowserInteraction)
        dev_info.setWordWrap(True)
        dev_layout.addWidget(dev_info)
        
        layout.addWidget(dev_group)
        
        # 项目链接组
        link_group = QGroupBox("🔗 项目链接")
        link_layout = QVBoxLayout(link_group)
        
        link_info = QLabel(
            f"<b style='color: #a29bfe;'>GitHub 仓库:</b><br>"
            f"<a href='https://github.com/9364953w-dotcom/image-compressor' style='color: #6c5ce7;'>"
            f"github.com/9364953w-dotcom/image-compressor</a><br><br>"
            f"<b style='color: #a29bfe;'>问题反馈:</b><br>"
            f"<a href='https://github.com/9364953w-dotcom/image-compressor/issues' style='color: #6c5ce7;'>"
            f"GitHub Issues</a>"
        )
        link_info.setOpenExternalLinks(True)
        link_info.setTextInteractionFlags(Qt.TextBrowserInteraction)
        link_info.setWordWrap(True)
        link_layout.addWidget(link_info)
        
        layout.addWidget(link_group)
        
        # 版权信息
        copyright_label = QLabel(
            f"© 2024 MWang. All Rights Reserved.<br>"
            f"许可证: MIT License"
        )
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet("color: #6b6b7b; font-size: 11px;")
        layout.addWidget(copyright_label)
        
        return tab
    
    def _create_tech_tab(self):
        """创建技术栈标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignTop)
        
        # 核心技术
        core_group = QGroupBox("🎯 核心技术")
        core_layout = QVBoxLayout(core_group)
        
        core_text = QTextEdit()
        core_text.setReadOnly(True)
        core_text.setMaximumHeight(140)
        core_text.setPlainText(
            "• Python 3.8+ - 编程语言\n"
            "• PyQt5 5.15+ - GUI 框架\n"
            "• Pillow 9.0+ - 图像处理库\n"
            "• Qt Fusion - 界面风格"
        )
        core_layout.addWidget(core_text)
        
        layout.addWidget(core_group)
        
        # 系统信息
        import platform
        from PyQt5.QtCore import QT_VERSION_STR
        
        sys_group = QGroupBox("💻 系统信息")
        sys_layout = QVBoxLayout(sys_group)
        
        sys_text = QTextEdit()
        sys_text.setReadOnly(True)
        sys_text.setMaximumHeight(100)
        sys_text.setPlainText(
            f"Python: {platform.python_version()}\n"
            f"Qt: {QT_VERSION_STR}\n"
            f"系统: {platform.system()} {platform.release()}\n"
            f"架构: {platform.machine()}"
        )
        sys_layout.addWidget(sys_text)
        
        layout.addWidget(sys_group)
        
        # 构建信息
        build_group = QGroupBox("📦 构建信息")
        build_layout = QVBoxLayout(build_group)
        
        build_label = QLabel(
            f"<b>版本:</b> {__version__}<br>"
            f"<b>构建日期:</b> 2024-03<br>"
            f"<b>打包工具:</b> PyInstaller"
        )
        build_label.setWordWrap(True)
        build_layout.addWidget(build_label)
        
        layout.addWidget(build_group)
        layout.addStretch()
        
        return tab
    
    def _create_thanks_tab(self):
        """创建致谢标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignTop)
        
        thanks_group = QGroupBox("❤️ 特别感谢")
        thanks_layout = QVBoxLayout(thanks_group)
        
        thanks_text = QTextEdit()
        thanks_text.setReadOnly(True)
        thanks_text.setPlainText(
            "特别感谢以下开源项目和社区:\n\n"
            "🎨 Qt Framework\n"
            "   跨平台的 GUI 应用程序框架\n"
            "   https://www.qt.io/\n\n"
            "🖼️ Pillow (PIL Fork)\n"
            "   Python 图像处理库\n"
            "   https://python-pillow.org/\n\n"
            "🐍 Python Software Foundation\n"
            "   Python 编程语言\n"
            "   https://www.python.org/\n\n"
            "🌟 PyQt5\n"
            "   Python 的 Qt 绑定\n\n"
            "❤️ 开源社区\n"
            "   感谢所有贡献者和用户的支持"
        )
        thanks_layout.addWidget(thanks_text)
        
        layout.addWidget(thanks_group)
        return tab
    
    def _open_github(self):
        """打开 GitHub 仓库"""
        QDesktopServices.openUrl(QUrl("https://github.com/9364953w-dotcom/image-compressor"))
