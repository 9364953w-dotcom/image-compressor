# 原生编码器

打包时按平台放入对应目录：

- `macos-arm64/cjpeg`、`macos-arm64/oxipng`
- `macos-x64/cjpeg`、`macos-x64/oxipng`
- `windows-x64/oxipng.exe`（`cjpeg.exe` 可选）

macOS / Linux 可运行：

```bash
tools/fetch_tools.sh
```

运行时会优先使用这些工具，找不到则回退 Pillow。
