"""오류 기록: logs/error.log.

pythonw로 실행하면(더블클릭 실행) 콘솔이 없어 오류 메시지가 사라지므로 파일에 남긴다.
오류가 없으면 파일을 만들지 않는다.
"""

from __future__ import annotations

import sys
import traceback
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "error.log"


def _open_log():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    return open(LOG_PATH, "a", encoding="utf-8")


def log_exception(exc_type, exc, tb, where: str = "") -> None:
    """오류 한 건을 시각과 함께 기록한다. 콘솔이 있으면 콘솔에도 보여 준다."""
    text = "".join(traceback.format_exception(exc_type, exc, tb))
    try:
        with _open_log() as f:
            f.write(f"\n===== {datetime.now():%Y-%m-%d %H:%M:%S} {where} =====\n{text}")
    except OSError:
        pass  # 기록조차 못 하면 어쩔 수 없다(앱은 계속 동작)
    if not isinstance(sys.stderr, _LazyLog) and sys.stderr is not None:
        sys.stderr.write(text)


class _LazyLog:
    """콘솔이 없을 때 stderr 대신 쓰는 파일. 처음 무언가 쓸 때만 파일을 연다."""

    def __init__(self):
        self._file = None

    def write(self, text: str) -> int:
        if not text:
            return 0
        try:
            if self._file is None:
                self._file = _open_log()
                self._file.write(f"\n===== {datetime.now():%Y-%m-%d %H:%M:%S} (stderr) =====\n")
            self._file.write(text)
            self._file.flush()
        except OSError:
            pass
        return len(text)

    def flush(self) -> None:
        if self._file is not None:
            self._file.flush()


def install() -> None:
    """콘솔이 없으면(pythonw) 경고나 남은 오류 출력도 기록 파일로 가게 한다."""
    if sys.stderr is None:
        sys.stderr = _LazyLog()
    sys.excepthook = lambda t, e, tb: log_exception(t, e, tb, "처리되지 않은 오류")
