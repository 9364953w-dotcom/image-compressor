"""
关于对话框 - 显示软件信息、作者、版权等
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QTextEdit, QGroupBox, QFrame,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QFont

from src.config import APP_NAME, __version__


class AboutDialog(QDialog):
    """关于对话框 - 完整版"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("关于")
        self.setMinimumSize(500, 450)
        self.resize(500, 500)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # ========== 软件标识区 ==========
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(8)
        
        # 软件名称
        name_label = QLabel(APP_NAME)
        name_font = QFont()
        name_font.setPointSize(18)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(name_label)
        
        # 版本号
        version_label = QLabel(f"版本 {__version__}")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #78909c;")
        header_layout.addWidget(version_label)
        
        # 简短描述
        desc_label = QLabel("简单高效的图片批量处理工具")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #b0bec5; font-style: italic;")
        header_layout.addWidget(desc_label)
        
        layout.addWidget(header_widget)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #455a64;")
        line.setFixedHeight(1)
        layout.addWidget(line)
        
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
        
        # 查看 GitHub 按钮
        github_btn = QPushButton("🌐 访问 GitHub")
        github_btn.clicked.connect(self._open_github)
        btn_layout.addWidget(github_btn)
        
        # 问题反馈按钮
        feedback_btn = QPushButton("🐛 问题反馈")
        feedback_btn.clicked.connect(self._open_issues)
        btn_layout.addWidget(feedback_btn)
        
        btn_layout.addSpacing(20)
        
        # 确定按钮
        ok_btn = QPushButton("确定")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setFixedWidth(80)
        btn_layout.addWidget(ok_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _create_info_tab(self):
        """创建信息标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignTop)
        
        # 开发者信息组
        dev_group = QGroupBox("👤 开发者信息")
        dev_layout = QVBoxLayout(dev_group)
        
        dev_info = QLabel(
            f"<b>开发者:</b> MWang<br>"
            f"<b>邮箱:</b> <a href='mailto:9364953@qq.com'>9364953@qq.com</a><br>"
            f"<b>GitHub:</b> <a href='https://github.com/9364953w-dotcom'>@9364953w-dotcom</a>"
        )
        dev_info.setOpenExternalLinks(True)
        dev_info.setTextInteractionFlags(Qt.TextBrowserInteraction)
        dev_layout.addWidget(dev_info)
        
        layout.addWidget(dev_group)
        
        # 项目链接组
        link_group = QGroupBox("🔗 项目链接")
        link_layout = QVBoxLayout(link_group)
        
        link_info = QLabel(
            f"<b>GitHub 仓库:</b><br>"
            f"<a href='https://github.com/9364953w-dotcom/image-compressor'>"
            f"https://github.com/9364953w-dotcom/image-compressor</a><br><br>"
            f"<b>问题反馈:</b><br>"
            f"<a href='https://github.com/9364953w-dotcom/image-compressor/issues'>"
            f"https://github.com/9364953w-dotcom/image-compressor/issues</a><br><br>"
            f"<b>使用文档:</b><br>"
            f"<a href='https://github.com/9364953w-dotcom/image-compressor#readme'>"
            f"查看 README 文档</a>"
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
        copyright_label.setStyleSheet("color: #78909c; font-size: 11px;")
        layout.addWidget(copyright_label)
        
        return tab
    
    def _create_tech_tab(self):
        """创建技术栈标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignTop)
        
        # 核心技术
        core_group = QGroupBox("🎯 核心技术")
        core_layout = QVBoxLayout(core_group)
        
        core_text = QTextEdit()
        core_text.setReadOnly(True)
        core_text.setMaximumHeight(120)
        core_text.setPlainText(
            "• Python 3.8+ - 编程语言\n"
            "• PyQt5 5.15+ - GUI 框架\n"
            "• Pillow 9.0+ - 图像处理库\n"
            "• Qt Fusion - 界面风格"
        )
        core_layout.addWidget(core_text)
        
        layout.addWidget(core_group)
        
        # 系统信息
        import sys
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
            f"<b>构建日期:</b> 2024-03-01<br>"
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
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignTop)
        
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
            "   Python 的 Qt 绑定\n"
            "   https://www.riverbankcomputing.com/\n\n"
            "❤️ 开源社区\n"
            "   感谢所有贡献者和用户的支持"
        )
        layout.addWidget(thanks_text)
        
        return tab
    
    def _open_github(self):
        """打开 GitHub 仓库"""
        QDesktopServices.openUrl(QUrl("https://github.com/9364953w-dotcom/image-compressor"))
    
    def _open_issues(self):
        """打开问题反馈页面"""
        QDesktopServices.openUrl(QUrl("https://github.com/9364953w-dotcom/image-compressor/issues"))
