#!/usr/bin/env python3
"""
版本发布工具

用法:
    python release.py <新版本号> [发布说明]
    
示例:
    python release.py 1.3.0 "新增批量水印功能"
    python release.py 1.2.1 "修复bug"
"""

import sys
import re
from pathlib import Path
from datetime import datetime


def update_file(filepath: Path, pattern: str, replacement: str) -> bool:
    """更新文件中的指定内容"""
    try:
        content = filepath.read_text(encoding='utf-8')
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            filepath.write_text(new_content, encoding='utf-8')
            print(f"  ✓ 更新: {filepath}")
            return True
        else:
            print(f"  - 无需更新: {filepath}")
            return False
    except Exception as e:
        print(f"  ✗ 错误: {filepath} - {e}")
        return False


def release(new_version: str, release_notes: str = ""):
    """执行版本发布"""
    print(f"\n🚀 开始发布 v{new_version}\n")
    
    # 1. 更新 config.py
    print("1. 更新 src/config.py")
    update_file(
        Path("src/config.py"),
        r'__version__ = "[\d.]+"',
        f'__version__ = "{new_version}"'
    )
    
    # 2. 更新 README.md
    print("\n2. 更新 README.md")
    update_file(
        Path("README.md"),
        r'^# 图片批量压缩工具 v[\d.]+',
        f'# 图片批量压缩工具 v{new_version}'
    )
    
    # 3. 更新 AGENTS.md
    print("\n3. 更新 AGENTS.md")
    update_file(
        Path("AGENTS.md"),
        r'\*\*版本\*\*: v[\d.]+',
        f'**版本**: v{new_version}'
    )
    
    print(f"\n✅ 版本 v{new_version} 更新完成！")
    print("\n接下来请执行:")
    print(f'  git add -A')
    print(f'  git commit -m "release: v{new_version} - {release_notes or "版本更新"}"')
    print(f'  git push origin main')


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    version = sys.argv[1]
    notes = sys.argv[2] if len(sys.argv) > 2 else ""
    
    release(version, notes)
