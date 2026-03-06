# AGENTS.md - 项目背景文档

> 本文档用于帮助 AI 助手快速了解项目背景，避免上下文丢失

## 项目概述

**项目名称**: 图片批量压缩工具  
**版本**: v1.3.3  
**GitHub**: https://github.com/9364953w-dotcom/image-compressor  

一个基于 PyQt5 的图形化图片批量压缩工具，支持多线程并行处理、智能压缩、格式转换等高级功能。

## 技术栈

- **GUI 框架**: PyQt5 (Qt Fusion 风格 + 自定义深色调色板)
- **图像处理**: Pillow (PIL)
- **打包工具**: PyInstaller
- **Python 版本**: 3.8+

## 项目结构

```
image-compressor/
├── src/
│   ├── __init__.py
│   ├── __main__.py          # 程序入口 (Fusion 风格 + 深色主题)
│   ├── config.py            # 配置常量 + ConfigManager (历史记录/缓存/预设)
│   ├── utils.py             # 工具函数 (format_bytes, setup_logging)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── compressor.py    # 图片压缩核心 (尺寸调整、格式转换、智能压缩、EXIF处理)
│   │   └── worker.py        # 多线程工作器 (智能线程控制、详细统计)
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── drag_drop.py     # 拖拽输入框
│   │   ├── about_dialog.py  # 关于对话框 (软件信息、作者、版权)
│   │   ├── exif_dialog.py   # EXIF查看对话框
│   │   └── main_window.py   # 主窗口 (所有 UI 组件和逻辑)
│   └── resources/
│       └── icon.icns        # 应用图标
├── 图片压缩工具.spec        # PyInstaller 打包配置
├── requirements.txt         # 依赖列表
├── README.md                # 项目说明文档
└── AGENTS.md                # 本文档
```

## 核心功能

### 基础功能
- 文件夹拖拽选择
- 支持格式: JPG、PNG、WebP、BMP、TIFF
- 覆盖模式 / 输出到指定文件夹
- 子文件夹递归处理
- 多线程并行压缩

### 高级功能 (v1.1.0)
1. **尺寸调整** - 限制最大宽度/高度，保持比例
2. **格式转换** - 转换为 JPG/PNG/WebP 或保持原格式
3. **智能压缩** - 自动寻找最佳质量参数达到目标文件大小
4. **历史记录** - 保存常用路径，下拉框快速选择
5. **批量重命名** - 支持序号、日期、前缀等命名模式
6. **详细统计** - 表格展示每个文件的压缩详情
7. **智能线程** - 根据文件大小动态调整线程数
8. **增量压缩** - 跳过已用相同设置处理过的文件

### 新增功能 (v1.2.0)
9. **预设配置** - 内置4种预设（网页用/手机分享/高质量存档/缩略图），支持自定义预设
10. **压缩预览** - 预览第一张图片的压缩效果，显示预估大小
11. **EXIF处理** - 保留/移除EXIF信息，自动旋转，查看EXIF详情

### 新增功能 (v1.3.0)
12. **UI重构** - 三栏布局（左文件源 / 中参数预览 / 右任务统计）
13. **实时预览联动** - 选中文件后自动预览，参数变化同步刷新
14. **预览体验升级** - 默认显示压缩后效果，支持 100% 细节对比
15. **窗口风格统一** - EXIF 与关于窗口统一主程序深色风格
16. **品牌标识** - 状态栏右侧固定展示“成都一禾视觉专用”

## UI 主题

当前使用 **Qt Fusion 风格** + **自定义深色调色板**：

```python
palette.setColor(QPalette.Window, QColor(53, 53, 53))      # #353535
palette.setColor(QPalette.Base, QColor(42, 42, 42))        # #2a2a2a
palette.setColor(QPalette.Highlight, QColor(42, 130, 218)) # #2a82da
palette.setColor(QPalette.Text, Qt.white)
```

## 配置和数据存储

- **历史记录**: `~/.image-compressor/.history.json` (最多10条)
- **增量缓存**: `~/.image-compressor/.compress_cache.json`
- **预设配置**: `~/.image-compressor/.presets.json`
- **日志文件**: `compress.log`

### 内置预设
1. **网页用** - 质量80%，宽度1920px，适合网站展示
2. **手机分享** - 质量75%，宽度1080px，目标200KB
3. **高质量存档** - 质量95%，保持原尺寸
4. **缩略图** - 质量60%，尺寸300x300

## 打包命令

### 本地打包

```bash
pyinstaller 图片压缩工具.spec
```

### GitHub Actions 自动构建

项目已配置 GitHub Actions 工作流 (`.github/workflows/build.yml`)：

**触发条件：**
- 推送到 main 分支
- 推送标签 `v*` (如 v1.2.0)
- 手动触发 (workflow_dispatch)

**构建产物：**
- **macOS**: `.app` 和 `.dmg`
- **Windows**: `.exe` 和 `.zip`

**自动发布：**
- 推送标签时自动创建 Release
- 自动上传构建产物到 Release

**手动触发构建：**
1. 进入 GitHub 仓库
2. 点击 Actions 标签
3. 选择 "Build Executables"
4. 点击 "Run workflow"

## 类说明

### CompressWorker (core/worker.py)
- 多线程工作器，使用 ThreadPoolExecutor
- 信号: progress, file_completed, result, finished
- 方法: calculate_optimal_workers() 动态线程控制

### compress_image (core/compressor.py)
- 单张图片压缩函数
- 支持: 尺寸调整、格式转换、智能压缩、重命名、增量检测
- 返回: (源路径, 状态, 原始大小, 新大小, 详细信息)

### ConfigManager (config.py)
- load_history() / save_history() - 历史记录管理
- load_cache() / save_cache() - 增量压缩缓存
- is_file_processed() / mark_file_processed() - 文件处理状态
- load_presets() / save_presets() - 预设配置管理
- save_custom_preset() - 保存自定义预设
- delete_preset() - 删除预设

### AboutDialog (widgets/about_dialog.py)
- 显示软件信息、开发者、版权、技术栈
- 3个标签页：信息/技术栈/致谢
- 可点击链接跳转 GitHub

### ExifDialog (widgets/exif_dialog.py)
- 显示图片 EXIF 信息
- 基本信息表：相机、日期、尺寸、GPS
- 完整 EXIF 数据查看

## 开发注意事项

1. **线程安全**: UI 更新必须通过信号，不要直接从工作线程操作 UI
2. **异常处理**: 所有文件操作需要 try-except 保护
3. **资源释放**: 线程和 worker 对象需要在 finished 信号中 deleteLater
4. **路径处理**: 使用 pathlib.Path，避免字符串拼接路径

## 版本管理

### 自动版本发布工具

项目包含 `release.py` 工具，用于统一更新版本号：

```bash
# 用法
python release.py <新版本号> [发布说明]

# 示例
python release.py 1.3.0 "新增批量水印功能"
```

该工具会自动更新以下文件中的版本号：
- `src/config.py` - 软件版本常量
- `README.md` - 文档标题
- `AGENTS.md` - 项目信息

### 对 AI 助手的指令

当你需要发布新版本时，可以对我说：

> "发布新版本 1.x.x，更新内容是 xxx"

我会自动执行：
1. 运行 `python release.py 1.x.x "xxx"`
2. 提交 Git 并推送
3. 确认所有文件已更新

## 最近修改记录

- `35c90db` - chore: 添加版本发布工具 release.py
- `aefe8d6` - docs: 更新 AGENTS.md 版本号到 v1.2.0
- `dbf75be` - docs: 更新 README 到 v1.2.0
- `be014c8` - feat: 添加预设配置、压缩预览、EXIF处理功能
- `71be911` - UI: 采用 Qt Fusion 风格 + 自定义深色调色板
- `ca8b0f5` - UI: 移除标签页外边框
- `93c3476` - UI: 采用 qdarkstyle 美化界面
- `df7b286` - UI: 修复样式问题，采用 Material Design 深色主题
- `30e8d87` - UI改进：醒目复选框、明确的历史记录标签、版本号标题
- `c7fc7a6` - fix: 修复闪退问题（Path 导入缺失）
- `ae22f16` - docs: 更新 README，添加 v1.1.0 新功能说明
- `171b467` - v1.1.0: 新增8大功能
- `c17d32a` - feat: 添加关于对话框（完整版）
- `fc35be3` - Initial commit: 图片批量压缩工具 v1.0.0
