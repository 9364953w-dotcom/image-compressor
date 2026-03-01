"""
应用程序入口点

使用方式:
    python -m src
    或直接运行: python src/__main__.py
"""

import sys

from PyQt5.QtWidgets import QApplication

from src.widgets import MainWindow
from src.config import APP_NAME


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName(APP_NAME)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
