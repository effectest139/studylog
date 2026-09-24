"""StudyLog 실행: python main.py [--data 경로]"""

from __future__ import annotations

import argparse
from pathlib import Path

from studylog.core import storage
from studylog.core.store import DataStore


def main() -> None:
    parser = argparse.ArgumentParser(description="StudyLog 공부 시간 기록")
    parser.add_argument("--data", type=Path, default=storage.DEFAULT_DATA_PATH,
                        help="데이터 JSON 파일 경로 (기본: data/studylog.json)")
    args = parser.parse_args()

    try:
        store = DataStore.open(args.data)
    except storage.NewerVersionError:
        import tkinter.messagebox as mb
        mb.showerror("StudyLog", "더 새 버전의 StudyLog가 만든 데이터 파일이에요.\n"
                                 "앱을 최신 버전으로 바꾼 뒤 열어 주세요.")
        return

    from studylog.ui.app import App  # 화면 코드는 데이터를 읽은 뒤에 불러온다
    App(store).mainloop()


if __name__ == "__main__":
    main()
