"""배포용 exe 만들기 (PyInstaller). Python이 없는 PC에서도 실행할 수 있다.

사용:
    pip install -r requirements.txt pyinstaller
    python tools/build_exe.py

결과:
    dist/StudyLog/StudyLog.exe            실행 파일(폴더째 있어야 실행된다)
    dist/StudyLog-<버전>-windows.zip      배포용 압축 파일(GitHub Releases에 올린다)

한 파일짜리(--onefile)는 켤 때마다 압축을 푸느라 몇 초씩 늦어서 폴더 방식으로 만든다.
exe로 실행하면 데이터는 %APPDATA%/StudyLog에 저장된다(studylog/core/storage.py).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import PyInstaller.__main__  # noqa: E402

from studylog import __version__  # noqa: E402

NAME = "StudyLog"
ICON = ROOT / "studylog" / "ui" / "assets" / "studylog.ico"


def build() -> Path:
    PyInstaller.__main__.run([
        str(ROOT / "main.py"),
        "--name", NAME,
        "--windowed",                 # 콘솔 창 없이(오류는 logs/error.log)
        "--onedir",
        "--noconfirm", "--clean",
        "--icon", str(ICON),
        # CustomTkinter의 테마(json)·글꼴 파일, 앱 아이콘
        "--collect-data", "customtkinter",
        "--add-data", f"{ICON.parent}{';'}studylog/ui/assets",
        # 앱에서 쓰지 않는 큰 모듈은 빼서 크기를 줄인다
        "--exclude-module", "pytest",
        "--exclude-module", "PyInstaller",
        "--exclude-module", "IPython",
        "--exclude-module", "PyQt5", "--exclude-module", "PyQt6",
        "--exclude-module", "PySide2", "--exclude-module", "PySide6",
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"),
    ])
    folder = ROOT / "dist" / NAME
    archive = shutil.make_archive(str(ROOT / "dist" / f"{NAME}-{__version__}-windows"), "zip",
                                  root_dir=folder.parent, base_dir=NAME)
    return Path(archive)


if __name__ == "__main__":
    zip_path = build()
    size = zip_path.stat().st_size / 1024 / 1024
    print(f"\n완료: {zip_path} ({size:.1f} MB)")
