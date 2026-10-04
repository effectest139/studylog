"""StudyLog 실행: python main.py [--data 경로]

더블클릭으로 실행하려면 'StudyLog 실행.bat'(실제 데이터) 또는 'StudyLog 시연용.bat'(가짜 데이터).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from studylog import errorlog
from studylog.core import storage
from studylog.core.store import DataStore


def _show_error(message: str) -> None:
    import tkinter.messagebox as mb
    mb.showerror("StudyLog", message)


def main() -> None:
    parser = argparse.ArgumentParser(description="StudyLog 공부 시간 기록")
    parser.add_argument("--data", type=Path, default=storage.DEFAULT_DATA_PATH,
                        help="데이터 JSON 파일 경로 (기본: data/studylog.json)")
    args = parser.parse_args()

    try:
        store = DataStore.open(args.data)
    except storage.NewerVersionError:
        _show_error("더 새 버전의 StudyLog가 만든 데이터 파일이에요.\n앱을 최신 버전으로 바꾼 뒤 열어 주세요.")
        return

    from studylog.ui.app import App  # 화면 코드는 데이터를 읽은 뒤에 불러온다
    App(store).mainloop()


if __name__ == "__main__":
    errorlog.install()
    try:
        main()
    except Exception:
        # 창을 띄우기 전이나 창이 닫힌 뒤의 오류: 기록하고 알린다
        errorlog.log_exception(*sys.exc_info(), where="실행 중 오류")
        _show_error(f"오류가 나서 StudyLog를 열지 못했어요.\n자세한 내용을 아래 파일에 기록했어요.\n{errorlog.LOG_PATH}")
        sys.exit(1)
