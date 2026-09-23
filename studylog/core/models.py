"""앱 데이터 모델과 JSON(dict) 변환."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

SCHEMA_VERSION = 1


def _to_iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


@dataclass
class Subject:
    id: str
    name: str
    color: str
    weekly_goal_minutes: int = 0
    created_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "weekly_goal_minutes": self.weekly_goal_minutes,
            "created_at": _to_iso(self.created_at) if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Subject:
        created = d.get("created_at")
        return cls(
            id=str(d["id"]),
            name=str(d["name"]),
            color=str(d["color"]),
            weekly_goal_minutes=int(d.get("weekly_goal_minutes", 0)),
            created_at=datetime.fromisoformat(created) if created else None,
        )


@dataclass
class Session:
    """공부 기록 1개. study_seconds는 일시정지를 뺀 실제 공부 시간."""

    id: str
    subject_id: str
    start: datetime
    end: datetime
    study_seconds: int

    @property
    def day(self) -> date:
        """기록이 속한 날짜. 자정을 넘겨도 시작한 날짜에 넣는다."""
        return self.start.date()

    @property
    def paused_seconds(self) -> int:
        return max(0, int((self.end - self.start).total_seconds()) - self.study_seconds)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "subject_id": self.subject_id,
            "start": _to_iso(self.start),
            "end": _to_iso(self.end),
            "study_seconds": self.study_seconds,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Session:
        return cls(
            id=str(d["id"]),
            subject_id=str(d["subject_id"]),
            start=datetime.fromisoformat(d["start"]),
            end=datetime.fromisoformat(d["end"]),
            study_seconds=int(d["study_seconds"]),
        )


@dataclass
class AppData:
    """JSON 파일 하나에 들어가는 전체 데이터."""

    profile_name: str | None = None  # None이면 첫 실행(온보딩) 전
    weekly_goal_minutes: int = 0
    subjects: list[Subject] = field(default_factory=list)
    sessions: list[Session] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": SCHEMA_VERSION,
            "profile": {"name": self.profile_name} if self.profile_name is not None else None,
            "weekly_goal_minutes": self.weekly_goal_minutes,
            "subjects": [s.to_dict() for s in self.subjects],
            "sessions": [s.to_dict() for s in self.sessions],
        }

    @classmethod
    def from_dict(cls, d: dict) -> AppData:
        """형식이 틀리면 KeyError/TypeError/ValueError가 난다(storage에서 처리)."""
        if not isinstance(d, dict):
            raise TypeError("최상위 값이 객체가 아닙니다")
        profile = d.get("profile")
        data = cls(
            profile_name=str(profile["name"]) if profile else None,
            weekly_goal_minutes=int(d.get("weekly_goal_minutes", 0)),
            subjects=[Subject.from_dict(s) for s in d.get("subjects", [])],
            sessions=[Session.from_dict(s) for s in d.get("sessions", [])],
        )
        # 없는 과목을 가리키는 기록은 버린다(손으로 고친 파일 대비)
        ids = {s.id for s in data.subjects}
        data.sessions = [s for s in data.sessions if s.subject_id in ids]
        return data
