"""DataStore: 데이터를 바꾸는 모든 동작. 바꿀 때마다 바로 파일에 저장한다.

화면 코드는 이 클래스의 메서드만 불러서 데이터를 바꾼다.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable

from . import storage
from .models import AppData, Session, Subject

MAX_SUBJECTS = 10
NAME_MAX_LEN = 10
MIN_SESSION_SECONDS = 60  # 1분 미만 기록은 저장하지 않는다


class ValidationError(ValueError):
    """사용자 입력이 규칙에 맞지 않는다. 메시지는 화면에 그대로 보여 줄 수 있다."""


# --- 입력 검사 (온보딩처럼 아직 저장하기 전 목록에도 쓰도록 함수로 둔다) ---

def check_name(name: str) -> str | None:
    """이름·과목명 공통 길이 검사. 문제가 없으면 None."""
    n = len(name.strip())
    if n < 1 or n > NAME_MAX_LEN:
        return f"1~{NAME_MAX_LEN}자로 입력해 주세요"
    return None


def check_subject_name(name: str, existing_names: Iterable[str]) -> str | None:
    """길이 + 중복 검사. existing_names에는 자기 자신을 빼고 넘긴다."""
    err = check_name(name)
    if err:
        return err
    key = name.strip().casefold()
    if any(key == e.strip().casefold() for e in existing_names):
        return "이미 있는 과목이에요"
    return None


@dataclass(frozen=True)
class ResetSummary:
    sessions: int
    subjects: int


class DataStore:
    def __init__(self, path: Path, data: AppData | None = None,
                 clock: Callable[[], datetime] = datetime.now):
        self.path = Path(path)
        self.data = data if data is not None else AppData()
        self._clock = clock
        self.recovered_backup: Path | None = None  # 깨진 파일을 옮겼으면 그 경로

    @classmethod
    def open(cls, path: Path = storage.DEFAULT_DATA_PATH, **kwargs) -> DataStore:
        """파일을 읽는다. 깨졌으면 옆으로 옮기고 빈 데이터로 시작한다.

        NewerVersionError는 그대로 올려 보낸다(덮어쓰면 안 되므로 화면에서 알리고 종료).
        """
        path = Path(path)
        try:
            return cls(path, storage.load(path), **kwargs)
        except storage.CorruptDataError:
            backup = storage.backup_corrupt(path)
            store = cls(path, AppData(), **kwargs)
            store.recovered_backup = backup
            return store

    def _save(self) -> None:
        storage.save(self.data, self.path)

    def _new_id(self, prefix: str, taken: Iterable[str]) -> str:
        taken = set(taken)
        while True:
            new = f"{prefix}_{secrets.token_hex(3)}"
            if new not in taken:
                return new

    # --- 읽기 ---

    @property
    def is_onboarded(self) -> bool:
        return self.data.profile_name is not None

    @property
    def name(self) -> str:
        return self.data.profile_name or ""

    @property
    def weekly_goal_minutes(self) -> int:
        return self.data.weekly_goal_minutes

    @property
    def subjects(self) -> list[Subject]:
        return list(self.data.subjects)

    @property
    def sessions(self) -> list[Session]:
        return list(self.data.sessions)

    def get_subject(self, subject_id: str) -> Subject:
        for s in self.data.subjects:
            if s.id == subject_id:
                return s
        raise KeyError(subject_id)

    def can_add_subject(self) -> bool:
        return len(self.data.subjects) < MAX_SUBJECTS

    def used_colors(self, exclude_id: str | None = None) -> list[str]:
        return [s.color for s in self.data.subjects if s.id != exclude_id]

    def check_subject_name(self, name: str, exclude_id: str | None = None) -> str | None:
        return check_subject_name(
            name, [s.name for s in self.data.subjects if s.id != exclude_id])

    def count_sessions(self, subject_id: str) -> int:
        return sum(1 for s in self.data.sessions if s.subject_id == subject_id)

    def reset_summary(self) -> ResetSummary:
        return ResetSummary(len(self.data.sessions), len(self.data.subjects))

    # --- 프로필·온보딩 ---

    def complete_onboarding(self, name: str, subjects: list[tuple[str, str]]) -> None:
        """첫 실행 2단계를 마쳤을 때 이름과 과목(이름, 색)을 한 번에 저장한다."""
        if err := check_name(name):
            raise ValidationError(err)
        if not subjects:
            raise ValidationError("과목을 1개 이상 추가해 주세요")
        if len(subjects) > MAX_SUBJECTS:
            raise ValidationError(f"과목은 최대 {MAX_SUBJECTS}개예요")
        new = AppData(profile_name=name.strip())
        for i, (sname, color) in enumerate(subjects):
            if err := check_subject_name(sname, [n for n, _ in subjects[:i]]):
                raise ValidationError(err)
            new.subjects.append(Subject(
                id=self._new_id("s", (s.id for s in new.subjects)),
                name=sname.strip(), color=color, created_at=self._clock()))
        self.data = new
        self._save()

    def set_name(self, name: str) -> None:
        if err := check_name(name):
            raise ValidationError(err)
        self.data.profile_name = name.strip()
        self._save()

    # --- 과목 ---

    def add_subject(self, name: str, color: str) -> Subject:
        if not self.can_add_subject():
            raise ValidationError(f"과목은 최대 {MAX_SUBJECTS}개예요")
        if err := self.check_subject_name(name):
            raise ValidationError(err)
        subject = Subject(
            id=self._new_id("s", (s.id for s in self.data.subjects)),
            name=name.strip(), color=color, created_at=self._clock())
        self.data.subjects.append(subject)
        self._save()
        return subject

    def update_subject(self, subject_id: str, name: str, color: str) -> None:
        subject = self.get_subject(subject_id)
        if err := self.check_subject_name(name, exclude_id=subject_id):
            raise ValidationError(err)
        subject.name = name.strip()
        subject.color = color
        self._save()

    def delete_subject(self, subject_id: str) -> int:
        """과목과 그 과목의 기록(목표 포함)을 지운다. 지운 기록 수를 돌려준다."""
        self.get_subject(subject_id)
        before = len(self.data.sessions)
        self.data.subjects = [s for s in self.data.subjects if s.id != subject_id]
        self.data.sessions = [s for s in self.data.sessions if s.subject_id != subject_id]
        self._save()
        return before - len(self.data.sessions)

    # --- 기록 ---

    def add_session(self, subject_id: str, start: datetime, end: datetime,
                    study_seconds: int) -> Session:
        self.get_subject(subject_id)
        study_seconds = int(study_seconds)
        if study_seconds < MIN_SESSION_SECONDS:
            raise ValidationError("1분 미만은 저장되지 않아요")
        if end < start:
            raise ValidationError("종료 시각이 시작 시각보다 빨라요")
        # 실제 공부 시간은 전체 경과 시간보다 길 수 없다
        study_seconds = min(study_seconds, int((end - start).total_seconds()))
        session = Session(
            id=self._new_id("r", (s.id for s in self.data.sessions)),
            subject_id=subject_id, start=start, end=end, study_seconds=study_seconds)
        self.data.sessions.append(session)
        self._save()
        return session

    def delete_session(self, session_id: str) -> None:
        before = len(self.data.sessions)
        self.data.sessions = [s for s in self.data.sessions if s.id != session_id]
        if len(self.data.sessions) == before:
            raise KeyError(session_id)
        self._save()

    # --- 목표 ---

    def set_goals(self, weekly_minutes: int, subject_minutes: dict[str, int]) -> None:
        """주간 전체 목표와 과목별 주간 목표(분). 과목별 합계가 전체보다 커도 된다."""
        values = [weekly_minutes, *subject_minutes.values()]
        if any(int(v) < 0 for v in values):
            raise ValidationError("목표는 0 이상이어야 해요")
        for sid in subject_minutes:
            self.get_subject(sid)
        self.data.weekly_goal_minutes = int(weekly_minutes)
        for s in self.data.subjects:
            if s.id in subject_minutes:
                s.weekly_goal_minutes = int(subject_minutes[s.id])
        self._save()

    # --- 초기화 ---

    def reset(self) -> None:
        """기록·목표·과목·이름을 모두 지운다. 다음 화면은 첫 실행 화면."""
        self.data = AppData()
        self._save()
