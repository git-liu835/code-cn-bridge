"""将 Python 后端打包为独立可执行文件（PyInstaller）"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist-backend"


def main():
    DIST.mkdir(exist_ok=True)

    pip = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-q"]

    # 确保基础工具链
    subprocess.check_call(pip + ["--upgrade", "pip", "setuptools", "wheel"])
    subprocess.check_call(pip + ["pyinstaller"])

    # 安装本项目及其依赖
    subprocess.check_call(pip + ["-e", str(ROOT)])

    # 创建临时入口脚本
    entry_dir = ROOT / "build"
    entry_dir.mkdir(exist_ok=True)
    entry = entry_dir / "_entry.py"
    entry.write_text("from code_cn_bridge.cli import main; main()", encoding="utf-8")

    # 收集 code_cn_bridge 包内所有子模块作为 hidden-import
    package_dir = ROOT / "code_cn_bridge"
    hidden_args = ["--hidden-import", "code_cn_bridge"]
    for py_file in sorted(package_dir.rglob("*.py")):
        if py_file.name == "__init__.py":
            continue
        rel = py_file.relative_to(ROOT)
        mod = str(rel.with_suffix("")).replace("/", ".").replace("\\", ".")
        hidden_args.extend(["--hidden-import", mod])

    # 隐式依赖
    extra_imports = [
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.protocols.http.auto",
        "fastapi",
        "starlette",
        "httpx",
        "click",
        "yaml",
        "watchfiles",
        "pydantic",
    ]
    for imp in extra_imports:
        hidden_args.extend(["--hidden-import", imp])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconfirm",
        "--clean",
        "--name", "code-cn-bridge",
        "--distpath", str(DIST),
        "--workpath", str(entry_dir / "pyinstaller"),
        "--specpath", str(entry_dir),
        "--collect-all", "code_cn_bridge",
        *hidden_args,
        str(entry),
    ]

    subprocess.check_call(cmd)

    ext = ".exe" if sys.platform == "win32" else ""
    output = DIST / f"code-cn-bridge{ext}"
    print(f"\nBackend built → {output}")


if __name__ == "__main__":
    main()
