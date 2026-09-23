import json
from datetime import datetime, timedelta

import pytest

from studylog.core import storage
from studylog.core.colors import PALETTE
from studylog.core.store import DataStore, ValidationError

T0 = datetime(2026, 9, 23, 19, 30)


@pytest.fixture
def path(tmp_path):
    return tmp_path / "data" / "studylog.json"


@pytest.fixture
def store(path):
    s = DataStore.open(path, clock=lambda: T0)
    s.complete_onboarding("김민지", [("수학", PALETTE[1]), ("영어", PALETTE[2])])
    return s


def subject_id(store, name):
    return next(s.id for s in store.subjects if s.name == name)


def test_new_file_starts_onboarding(path):
    s = DataStore.open(path)
    assert not s.is_onboarded
    assert not path.exists()


def test_onboarding_saves_and_reloads(store, path):
    again = DataStore.open(path)
    assert again.is_onboarded
    assert again.name == "김민지"
    assert [s.name for s in again.subjects] == ["수학", "영어"]


def test_onboarding_needs_a_subject(path):
    with pytest.raises(ValidationError):
        DataStore.open(path).complete_onboarding("김민지", [])


def test_onboarding_rejects_duplicate_subjects(path):
    with pytest.raises(ValidationError):
        DataStore.open(path).complete_onboarding("a", [("수학", "#000000"), ("수학 ", "#111111")])


@pytest.mark.parametrize("name", ["", "   ", "가" * 11])
def test_name_length(store, name):
    with pytest.raises(ValidationError):
        store.set_name(name)


def test_name_is_trimmed(store):
    store.set_name("  민지  ")
    assert store.name == "민지"


def test_subject_limit_is_ten(store):
    for i in range(8):
        store.add_subject(f"과목{i}", PALETTE[i])
    assert len(store.subjects) == 10
    assert not store.can_add_subject()
    with pytest.raises(ValidationError):
        store.add_subject("하나 더", PALETTE[0])


def test_duplicate_subject_name(store):
    assert store.check_subject_name("수학") == "이미 있는 과목이에요"
    with pytest.raises(ValidationError):
        store.add_subject(" 수학", PALETTE[5])
    # 자기 자신 이름으로 수정하는 것은 괜찮다
    sid = subject_id(store, "수학")
    store.update_subject(sid, "수학", PALETTE[6])
    assert store.get_subject(sid).color == PALETTE[6]


def test_delete_subject_removes_its_sessions(store, path):
    math, eng = subject_id(store, "수학"), subject_id(store, "영어")
    for i in range(3):
        store.add_session(math, T0 + timedelta(days=i), T0 + timedelta(days=i, hours=1), 3600)
    store.add_session(eng, T0, T0 + timedelta(minutes=30), 1800)

    assert store.count_sessions(math) == 3
    assert store.delete_subject(math) == 3

    again = DataStore.open(path)
    assert [s.name for s in again.subjects] == ["영어"]
    assert len(again.sessions) == 1


def test_short_session_is_rejected(store):
    with pytest.raises(ValidationError):
        store.add_session(subject_id(store, "수학"), T0, T0 + timedelta(seconds=59), 59)


def test_session_keeps_pause_out(store, path):
    sid = subject_id(store, "수학")
    store.add_session(sid, T0, T0 + timedelta(minutes=78, seconds=10), 4365)
    s = DataStore.open(path).sessions[0]
    assert s.study_seconds == 4365
    assert s.paused_seconds == 78 * 60 + 10 - 4365


def test_session_past_midnight_belongs_to_start_day(store):
    start = datetime(2026, 9, 23, 23, 30)
    s = store.add_session(subject_id(store, "수학"), start, start + timedelta(hours=1), 3600)
    assert s.day == start.date()


def test_delete_session(store, path):
    sid = subject_id(store, "수학")
    a = store.add_session(sid, T0, T0 + timedelta(hours=1), 3600)
    store.add_session(sid, T0, T0 + timedelta(hours=2), 7200)
    store.delete_session(a.id)
    assert [s.study_seconds for s in DataStore.open(path).sessions] == [7200]
    with pytest.raises(KeyError):
        store.delete_session(a.id)


def test_goals(store, path):
    math = subject_id(store, "수학")
    store.set_goals(720, {math: 900})  # 과목 합계가 전체보다 커도 저장된다
    again = DataStore.open(path)
    assert again.weekly_goal_minutes == 720
    assert again.get_subject(math).weekly_goal_minutes == 900
    with pytest.raises(ValidationError):
        store.set_goals(-1, {})


def test_reset(store, path):
    store.add_session(subject_id(store, "수학"), T0, T0 + timedelta(hours=1), 3600)
    summary = store.reset_summary()
    assert (summary.sessions, summary.subjects) == (1, 2)
    store.reset()
    again = DataStore.open(path)
    assert not again.is_onboarded
    assert again.subjects == [] and again.sessions == []


def test_corrupt_file_is_backed_up(path):
    path.parent.mkdir(parents=True)
    path.write_text("{ 깨진 json", encoding="utf-8")
    s = DataStore.open(path)
    assert not s.is_onboarded
    assert s.recovered_backup is not None and s.recovered_backup.exists()
    assert not path.exists()


def test_wrong_shape_counts_as_corrupt(path):
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"version": 1, "subjects": [{"name": "x"}]}), encoding="utf-8")
    assert DataStore.open(path).recovered_backup is not None


def test_newer_version_is_not_overwritten(path):
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"version": 99}), encoding="utf-8")
    with pytest.raises(storage.NewerVersionError):
        DataStore.open(path)
    assert path.exists()


def test_saved_json_shape(store, path):
    store.add_session(subject_id(store, "수학"), T0, T0 + timedelta(hours=1), 3500)
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["version"] == 1
    assert raw["profile"] == {"name": "김민지"}
    assert raw["sessions"][0]["start"] == "2026-09-23T19:30:00"
    assert raw["sessions"][0]["study_seconds"] == 3500
    assert not path.with_name(path.name + ".tmp").exists()
