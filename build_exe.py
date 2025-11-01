"""EXEファイルをビルドするスクリプト."""

import subprocess
import sys
from pathlib import Path


def build_exe():
    """PyInstallerでEXEファイルをビルドする."""
    print("EXEファイルをビルドしています...")

    # build_exe.specファイルを使ってビルド
    spec_file = Path(__file__).parent / "build_exe.spec"

    try:
        subprocess.run(
            ["poetry", "run", "pyinstaller", "--clean", str(spec_file)],
            check=True,
        )
        print("\nビルド完了!")
        print("実行ファイルは dist/ImageToPDF.exe に生成されました。")
    except subprocess.CalledProcessError as e:
        print(f"\nビルドエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()
