@echo off
REM 完整构建流水线：Python 后端 → Electron 桌面应用 → 安装包 (Windows)
setlocal

echo === code CN Bridge 构建流水线 ===

REM ── 1. 构建 Python 后端 ──────────────────────────────────────────
echo.
echo [1/3] 构建 Python 后端 (PyInstaller)...
python scripts\build-backend.py
if %errorlevel% neq 0 exit /b %errorlevel%

REM ── 2. 构建 Electron 前端 ────────────────────────────────────────
echo.
echo [2/3] 构建 Electron 前端...
cd desktop
call npm install
call npm run build
if %errorlevel% neq 0 exit /b %errorlevel%

REM ── 3. 打包桌面安装程序 ──────────────────────────────────────────
echo.
echo [3/3] 打包桌面安装程序 (electron-builder)...
call npx electron-builder --config electron-builder.yml
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo === 构建完成 ===
echo 安装包位于: desktop\release\
dir desktop\release\ 2>nul
