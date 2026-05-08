#!/usr/bin/env bash
# 完整构建流水线：Python 后端 → Electron 桌面应用 → 安装包
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "=== code CN Bridge 构建流水线 ==="
echo "Root: $ROOT"

# ── 1. 构建 Python 后端 ──────────────────────────────────────────
echo ""
echo "[1/3] 构建 Python 后端 (PyInstaller)..."
cd "$ROOT"
python scripts/build-backend.py

# ── 2. 构建 Electron 前端 ────────────────────────────────────────
echo ""
echo "[2/3] 构建 Electron 前端..."
cd "$ROOT/desktop"
npm install
npm run build

# ── 3. 打包桌面安装程序 ──────────────────────────────────────────
echo ""
echo "[3/3] 打包桌面安装程序 (electron-builder)..."
npx electron-builder --config electron-builder.yml

echo ""
echo "=== 构建完成 ==="
echo "安装包位于: $ROOT/desktop/release/"
ls -la "$ROOT/desktop/release/" 2>/dev/null || echo "(无文件)"
