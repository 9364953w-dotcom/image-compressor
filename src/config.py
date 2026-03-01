"""
应用程序配置模块
"""

from pathlib import Path

# 版本信息
__version__ = "1.0.0"
APP_NAME = "图片批量压缩工具"
BUNDLE_ID = "com.wang.imagecompressor"

# 支持的图片格式
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}

# 压缩参数默认值
DEFAULT_QUALITY = 90
DEFAULT_MIN_SIZE_MB = 0.1
DEFAULT_COMPRESS_LEVEL_PNG = 6  # PNG 压缩级别 1-9
DEFAULT_WEBP_METHOD = 6

# 工作线程配置
MAX_WORKERS = None  # None 表示使用 os.cpu_count()

# 资源路径
RESOURCES_DIR = Path(__file__).parent / "resources"
ICON_PATH = RESOURCES_DIR / "icon.icns"

# 日志配置
LOG_FILE = "compress.log"
LOG_LEVEL = "ERROR"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
