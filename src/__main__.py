"""
应用程序入口点 - 使用 Qt Fusion 风格

使用方式:
    python -m src
    或直接运行: python src/__main__.py
"""

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QStyleFactory

from src.widgets import MainWindow
from src.config import APP_NAME


def main():
    """主函数"""
    # 启用高 DPI 支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    
    # 使用 Qt Fusion 风格（跨平台最一致的现代风格）
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # 应用深色调色板
    from PyQt5.QtGui import QPalette, QColor
    palette = QPalette()
    
    # 深色主题配色
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(42, 42, 42))
    palette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(128, 128, 128))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(128, 128, 128))
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(128, 128, 128))
    
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
