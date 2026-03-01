"""
应用程序入口点

使用方式:
    python -m src
    或直接运行: python src/__main__.py
"""

import sys

import qdarkstyle
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from src.widgets import MainWindow
from src.config import APP_NAME


def main():
    """主函数"""
    # 启用高 DPI 支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    
    # 应用 Qt Modern Dark Theme
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
