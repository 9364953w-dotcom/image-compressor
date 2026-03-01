# 图片批量压缩工具

一个基于 PyQt5 的图形化图片批量压缩工具，支持多线程并行处理。

## 功能特性

- 📁 支持文件夹拖拽选择
- 🖼️ 支持多种格式：JPG、PNG、WebP、BMP、TIFF
- 🔄 覆盖模式：可选择输出文件夹或直接覆盖原文件
- 📂 支持子文件夹递归处理
- ⚡ 多线程并行压缩
- 📊 实时进度显示和统计
- 🎚️ 可调节压缩质量

## 项目结构

```
image-compressor/
├── src/
│   ├── __init__.py
│   ├── __main__.py          # 程序入口
│   ├── config.py            # 配置常量
│   ├── utils.py             # 工具函数
│   ├── core/
│   │   ├── __init__.py
│   │   ├── compressor.py    # 图片压缩核心
│   │   └── worker.py        # 多线程工作器
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── drag_drop.py     # 拖拽输入框
│   │   └── main_window.py   # 主窗口
│   └── resources/
│       └── icon.icns        # 应用图标
├── 图片压缩工具.spec        # PyInstaller 打包配置
├── README.md
└── .gitignore
```

## 安装依赖

```bash
pip install PyQt5 Pillow
```

## 运行方式

### 开发运行

```bash
# 进入项目目录
cd image-compressor

# 安装依赖
pip install -r requirements.txt

# 运行程序
python -m src
```

### 打包为可执行文件

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包
pyinstaller 图片压缩工具.spec

# 打包产物位于 dist/ 目录
```

## 使用说明

1. **选择输入文件夹**：点击"浏览..."按钮或拖拽文件夹到输入框
2. **选择输出文件夹**（可选）：
   - 选择输出文件夹：压缩后的图片保存到该文件夹
   - 留空：直接覆盖原文件（会弹出确认提示）
3. **设置选项**：
   - 包含子文件夹：是否递归处理子文件夹中的图片
   - 压缩质量：1-100，数值越大质量越好，文件越大
   - 最小文件大小：小于此值的文件将被跳过
4. **开始压缩**：点击"开始压缩"按钮

## 压缩效果

- JPG/WebP：通过调节质量参数控制压缩比
- PNG：使用 optimize 和压缩级别优化
- 通常可减少 30%-70% 的文件大小

## 技术栈

- Python 3.8+
- PyQt5 - GUI 框架
- Pillow - 图像处理
- PyInstaller - 打包工具

## 许可证

MIT License
