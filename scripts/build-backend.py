"""将 Python 后端打包为独立可执行文件（PyInstaller）"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist-backend"


def main():
    DIST.mkdir(exist_ok=True)

    # 确保 PyInstaller 已安装
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 先安装本项目（开发模式），让 PyInstaller 能发现 code_cn_bridge 包
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", str(ROOT)])

    # 创建临时入口脚本
    entry = ROOT / "build" / "_entry.py"
    entry.parent.mkdir(exist_ok=True)
    entry.write_text("from code_cn_bridge.cli import main; main()")

    # 发现所有子模块
    package_dir = ROOT / "code_cn_bridge"
    hidden_imports = []
    for py_file in package_dir.rglob("*.py"):
        if py_file.name == "__init__":
            continue
        rel = py_file.relative_to(ROOT)
        mod = str(rel.with_suffix("")).replace("/", ".").replace("\\", ".")
        hidden_imports.append(mod)

    hidden_args = []
    for mod in hidden_imports:
        hidden_args.extend(["--hidden-import", mod])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "code-cn-bridge",
        "--distpath", str(DIST),
        "--workpath", str(ROOT / "build" / "pyinstaller"),
        "--specpath", str(ROOT / "build"),
        "--hidden-import", "code_cn_bridge",
        *hidden_args,
        "--collect-all", "code_cn_bridge",
        str(entry),
    ]

    subprocess.check_call(cmd)
    print(f"\nBackend built → {DIST / 'code-cn-bridge'}{'.exe' if sys.platform == 'win32' else ''}")


if __name__ == "__main__":
    main()
