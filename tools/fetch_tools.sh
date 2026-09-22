#!/usr/bin/env bash
# 下载/复制当前平台的 mozjpeg(cjpeg) 与 oxipng，供打包使用。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OXIPNG_VERSION="${OXIPNG_VERSION:-9.1.5}"

uname_s="$(uname -s)"
uname_m="$(uname -m)"

if [[ "$uname_s" == "Darwin" ]]; then
  if [[ "$uname_m" == "arm64" ]]; then
    DEST="$ROOT/tools/macos-arm64"
    OXIPNG_ASSET="oxipng-${OXIPNG_VERSION}-aarch64-apple-darwin.tar.gz"
  else
    DEST="$ROOT/tools/macos-x64"
    OXIPNG_ASSET="oxipng-${OXIPNG_VERSION}-x86_64-apple-darwin.tar.gz"
  fi
elif [[ "$uname_s" == "Linux" ]]; then
  DEST="$ROOT/tools/linux-x64"
  OXIPNG_ASSET="oxipng-${OXIPNG_VERSION}-x86_64-unknown-linux-gnu.tar.gz"
else
  echo "请在 Windows 上使用 GitHub Actions 步骤下载工具。"
  exit 1
fi

mkdir -p "$DEST"

if [[ ! -x "$DEST/cjpeg" ]]; then
  if command -v brew >/dev/null 2>&1; then
    brew list mozjpeg >/dev/null 2>&1 || brew install mozjpeg || true
    MOZJPEG_PREFIX="$(brew --prefix mozjpeg 2>/dev/null || true)"
    if [[ -n "$MOZJPEG_PREFIX" && -x "$MOZJPEG_PREFIX/bin/cjpeg" ]]; then
      cp "$MOZJPEG_PREFIX/bin/cjpeg" "$DEST/cjpeg"
      chmod +x "$DEST/cjpeg"
    fi
  fi
  if [[ ! -x "$DEST/cjpeg" ]] && command -v cjpeg >/dev/null 2>&1; then
    cp "$(command -v cjpeg)" "$DEST/cjpeg"
    chmod +x "$DEST/cjpeg"
  fi
fi

if [[ ! -x "$DEST/oxipng" ]]; then
  TMP="$(mktemp -d)"
  URL="https://github.com/oxipng/oxipng/releases/download/v${OXIPNG_VERSION}/${OXIPNG_ASSET}"
  curl -fsSL "$URL" -o "$TMP/oxipng.tgz"
  tar -xzf "$TMP/oxipng.tgz" -C "$TMP"
  FOUND="$(find "$TMP" -type f -name oxipng | head -n 1)"
  if [[ -n "$FOUND" ]]; then
    cp "$FOUND" "$DEST/oxipng"
    chmod +x "$DEST/oxipng"
  fi
  rm -rf "$TMP"
fi

echo "tools ready in $DEST"
ls -l "$DEST"
