"""JSON 파일 읽기/쓰기."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

from .models import SCHEMA_VERSION, AppData

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "studylog.json"


class CorruptDataError(Exception):
    """파일을 읽을 수 없거나 형식이 틀렸다."""


class NewerVersionError(Exception):
    """더 새 버전의 앱이 만든 파일이다. 덮어쓰면 안 된다."""


def load(path: Path) -> AppData:
    """파일이 없으면 빈 데이터를 돌려준다."""
    if not path.exists():
        return AppData()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise CorruptDataError(str(e)) from e
    if isinstance(raw, dict) and int(raw.get("version", 1)) > SCHEMA_VERSION:
        raise NewerVersionError(f"파일 버전 {raw['version']}")
    try:
        return AppData.from_dict(raw)
    except (KeyError, TypeError, ValueError) as e:
        raise CorruptDataError(str(e)) from e


def backup_corrupt(path: Path) -> Path:
    """깨진 파일을 옆에 다른 이름으로 옮겨 둔다. 옮긴 경로를 돌려준다."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = path.with_name(f"{path.stem}.corrupt-{stamp}{path.suffix}")
    os.replace(path, target)
    return target


def save(data: AppData, path: Path) -> None:
    """임시 파일에 다 쓴 뒤 바꿔 끼워서, 쓰는 도중 꺼져도 원래 파일이 남게 한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    # OneDrive 등이 파일을 잠깐 잡고 있으면 교체가 실패할 수 있어 몇 번 다시 시도한다
    for attempt in range(5):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.1)
