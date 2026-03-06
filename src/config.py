"""
应用程序配置模块
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any

# 版本信息
__version__ = "1.3.5"
APP_NAME = "图片批量压缩工具"
BUNDLE_ID = "com.wang.imagecompressor"

# 支持的图片格式
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}
OUTPUT_FORMATS = ['original', 'jpg', 'png', 'webp']

# 压缩参数默认值
DEFAULT_QUALITY = 90
DEFAULT_MIN_SIZE_MB = 0.1
DEFAULT_COMPRESS_LEVEL_PNG = 6
DEFAULT_WEBP_METHOD = 6

# 尺寸调整默认值
DEFAULT_MAX_WIDTH = 0  # 0 表示不限制
DEFAULT_MAX_HEIGHT = 0
DEFAULT_KEEP_RATIO = True

# 工作线程配置
MAX_WORKERS = None  # None 表示使用 os.cpu_count()
DYNAMIC_THREADING = True  # 启用动态线程控制

# 智能压缩配置
SMART_COMPRESSION = True  # 启用智能压缩
SMART_TARGET_SIZES = [50, 100, 200, 500]  # 目标大小(KB)用于智能选择质量
SMART_TOLERANCE = 0.1  # 容差比例

# 增量压缩配置
INCREMENTAL_COMPRESSION = True  # 启用增量压缩
CACHE_FILE = ".compress_cache.json"

# 历史记录配置
HISTORY_FILE = ".history.json"
MAX_HISTORY_ITEMS = 10

# 预设配置
PRESETS_FILE = ".presets.json"
UI_SETTINGS_FILE = ".ui_settings.json"
DEFAULT_PRESETS = [
    {
        "name": "网页用",
        "description": "适合网站展示，平衡质量和大小",
        "settings": {
            "quality": 80,
            "output_format": "original",
            "max_width": 1920,
            "max_height": 0,
            "keep_ratio": True,
            "smart_mode": False,
            "target_size_kb": 0,
            "min_size_mb": 0.1,
        }
    },
    {
        "name": "手机分享",
        "description": "适合微信/微博分享，文件小巧",
        "settings": {
            "quality": 75,
            "output_format": "jpg",
            "max_width": 1080,
            "max_height": 1080,
            "keep_ratio": True,
            "smart_mode": True,
            "target_size_kb": 200,
            "min_size_mb": 0.0,
        }
    },
    {
        "name": "高质量存档",
        "description": "高质量保留，适合长期保存",
        "settings": {
            "quality": 95,
            "output_format": "original",
            "max_width": 0,
            "max_height": 0,
            "keep_ratio": True,
            "smart_mode": False,
            "target_size_kb": 0,
            "min_size_mb": 0.5,
        }
    },
    {
        "name": "缩略图",
        "description": "小尺寸缩略图，快速预览",
        "settings": {
            "quality": 60,
            "output_format": "jpg",
            "max_width": 300,
            "max_height": 300,
            "keep_ratio": True,
            "smart_mode": False,
            "target_size_kb": 0,
            "min_size_mb": 0.0,
        }
    },
]

# 批量重命名配置
RENAME_PATTERNS = [
    "{name}",           # 保持原文件名
    "{name}_{index:03d}",  # 原文件名_序号
    "{index:03d}",      # 纯序号
    "{prefix}{index:03d}",  # 自定义前缀+序号
    "{date}_{index:03d}",  # 日期+序号
]

# 资源路径
RESOURCES_DIR = Path(__file__).parent / "resources"
ICON_PATH = RESOURCES_DIR / "icon.icns"

# 日志配置
LOG_FILE = "compress.log"
LOG_LEVEL = "ERROR"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class ConfigManager:
    """配置管理器 - 处理历史记录和缓存"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".image-compressor"
        self.config_dir.mkdir(exist_ok=True)
        self.history_file = self.config_dir / HISTORY_FILE
        self.cache_file = self.config_dir / CACHE_FILE
        self.ui_settings_file = self.config_dir / UI_SETTINGS_FILE
    
    def load_history(self) -> List[Dict[str, Any]]:
        """加载历史记录"""
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    
    def save_history(self, history: List[Dict[str, Any]]) -> None:
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history[-MAX_HISTORY_ITEMS:], f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def add_history_item(self, input_path: str, output_path: str, settings: dict) -> None:
        """添加历史记录项"""
        history = self.load_history()
        history.append({
            "input_path": input_path,
            "output_path": output_path,
            "settings": settings,
        })
        self.save_history(history)
    
    def load_cache(self) -> Dict[str, Any]:
        """加载缓存（用于增量压缩）"""
        if not self.cache_file.exists():
            return {}
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def save_cache(self, cache: Dict[str, Any]) -> None:
        """保存缓存"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def get_file_hash(self, file_path: Path) -> str:
        """获取文件哈希（用于增量压缩判断）"""
        import hashlib
        try:
            stat = file_path.stat()
            # 使用文件路径+修改时间+大小作为哈希
            content = f"{file_path}:{stat.st_mtime}:{stat.st_size}"
            return hashlib.md5(content.encode()).hexdigest()
        except Exception:
            return ""
    
    def is_file_processed(self, file_path: Path, settings: dict) -> bool:
        """检查文件是否已使用相同设置处理过"""
        if not INCREMENTAL_COMPRESSION:
            return False
        
        cache = self.load_cache()
        file_hash = self.get_file_hash(file_path)
        
        if file_hash in cache:
            cached = cache[file_hash]
            # 检查设置是否相同
            if cached.get("settings") == settings:
                return True
        return False
    
    def mark_file_processed(self, file_path: Path, settings: dict, output_info: dict) -> None:
        """标记文件已处理"""
        if not INCREMENTAL_COMPRESSION:
            return
        
        cache = self.load_cache()
        file_hash = self.get_file_hash(file_path)
        cache[file_hash] = {
            "settings": settings,
            "output": output_info,
            "timestamp": os.path.getmtime(file_path) if file_path.exists() else 0,
        }
        # 限制缓存大小
        if len(cache) > 10000:
            # 删除最早的 20%
            sorted_items = sorted(cache.items(), key=lambda x: x[1].get("timestamp", 0))
            cache = dict(sorted_items[int(len(cache) * 0.2):])
        self.save_cache(cache)
    
    # ========== 预设管理 ==========
    
    def load_presets(self) -> list:
        """加载预设配置"""
        presets_file = self.config_dir / PRESETS_FILE
        if not presets_file.exists():
            return DEFAULT_PRESETS.copy()
        try:
            with open(presets_file, 'r', encoding='utf-8') as f:
                custom_presets = json.load(f)
                # 合并默认预设和自定义预设
                all_presets = DEFAULT_PRESETS.copy()
                all_presets.extend(custom_presets)
                return all_presets
        except Exception:
            return DEFAULT_PRESETS.copy()
    
    def save_presets(self, presets: list) -> None:
        """保存自定义预设（只保存非默认预设）"""
        presets_file = self.config_dir / PRESETS_FILE
        try:
            # 过滤掉默认预设，只保存自定义的
            default_names = {p["name"] for p in DEFAULT_PRESETS}
            custom_presets = [p for p in presets if p["name"] not in default_names]
            with open(presets_file, 'w', encoding='utf-8') as f:
                json.dump(custom_presets, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def save_custom_preset(self, name: str, description: str, settings: dict) -> bool:
        """保存自定义预设"""
        try:
            presets = self.load_presets()
            # 检查是否已存在
            for preset in presets:
                if preset["name"] == name:
                    preset["description"] = description
                    preset["settings"] = settings
                    break
            else:
                presets.append({
                    "name": name,
                    "description": description,
                    "settings": settings,
                })
            self.save_presets(presets)
            return True
        except Exception:
            return False
    
    def delete_preset(self, name: str) -> bool:
        """删除预设（不能删除默认预设）"""
        default_names = {p["name"] for p in DEFAULT_PRESETS}
        if name in default_names:
            return False
        try:
            presets = self.load_presets()
            presets = [p for p in presets if p["name"] != name]
            self.save_presets(presets)
            return True
        except Exception:
            return False

    # ========== UI 偏好 ==========

    def load_ui_settings(self) -> Dict[str, Any]:
        """加载 UI 偏好配置"""
        if not self.ui_settings_file.exists():
            return {}
        try:
            with open(self.ui_settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_ui_settings(self, settings: Dict[str, Any]) -> None:
        """保存 UI 偏好配置"""
        try:
            with open(self.ui_settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


# 全局配置管理器实例
config_manager = ConfigManager()
