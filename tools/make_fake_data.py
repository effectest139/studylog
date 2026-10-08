"""개발용 가짜 공부 기록 만들기 (앱 화면에는 없는 기능).

사용 예:
    python tools/make_fake_data.py                     # data/dev.json, 최근 70일
    python tools/make_fake_data.py --days 30 --seed 7  # 기간·난수 바꾸기
    python tools/make_fake_data.py --days 2            # 조언이 숨겨지는지(3일 미만) 확인
    python main.py --data data/dev.json                # 만든 파일로 앱 실행

실제 데이터(data/studylog.json)에는 쓰지 않는다.
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from studylog.core import storage  # noqa: E402
from studylog.core.colors import PALETTE  # noqa: E402
from studylog.core.models import AppData, Session, Subject  # noqa: E402

DEFAULT_OUT = storage.PROJECT_ROOT / "data" / "dev.json"
SUBJECTS = [("컴퓨터", 240), ("수학", 240), ("영어", 120), ("국어", 120), ("과학", 60)]
# 과목마다 공부하는 빈도(가중치)를 달리해 분석 화면에 차이가 보이게 한다
WEIGHTS = [5, 4, 3, 2, 1]


def make(days: int, seed: int, now: datetime) -> AppData:
    rng = random.Random(seed)
    data = AppData(profile_name="테스트", weekly_goal_minutes=720)
    for i, (name, goal) in enumerate(SUBJECTS):
        data.subjects.append(Subject(f"s_fake{i}", name, PALETTE[i], goal, now - timedelta(days=days)))

    n = 0
    today = now.date()
    for back in range(days - 1, -1, -1):
        day = today - timedelta(days=back)
        # 대체로 공부하고, 가끔 쉬는 날이 있다(주말엔 조금 더 쉰다)
        rest = 0.35 if day.weekday() >= 5 else 0.15
        if back > 0 and rng.random() < rest:
            continue
        hour = rng.choice([9, 13, 16, 19, 20, 21])
        start = datetime(day.year, day.month, day.day, hour, rng.choice([0, 10, 20, 30, 40]))
        for _ in range(rng.choice([1, 1, 2, 2, 3])):
            minutes = rng.randint(15, 95)
            paused = rng.choice([0, 0, 0, 3, 5, 10])
            end = start + timedelta(minutes=minutes + paused)
            if end > now:  # 오늘 기록은 지금보다 늦게 끝나면 안 된다
                break
            subject = rng.choices(data.subjects, weights=WEIGHTS)[0]
            n += 1
            data.sessions.append(Session(f"r_fake{n}", subject.id, start, end, minutes * 60))
            start = end + timedelta(minutes=rng.randint(10, 60))
            if start.date() != day:
                break
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="StudyLog 개발용 가짜 기록 만들기")
    parser.add_argument("--days", type=int, default=70, help="오늘부터 거슬러 올라갈 날 수 (기본 70)")
    parser.add_argument("--seed", type=int, default=1, help="난수 시드 (같으면 같은 데이터)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="저장할 파일 (기본 data/dev.json)")
    args = parser.parse_args()

    out = args.out.resolve()
    if out == storage.DEFAULT_DATA_PATH.resolve():
        parser.error("실제 데이터 파일(data/studylog.json)에는 쓸 수 없어요. 다른 경로를 주세요.")
    if args.days < 1:
        parser.error("--days는 1 이상이어야 해요.")

    data = make(args.days, args.seed, datetime.now().replace(second=0, microsecond=0))
    storage.save(data, out)
    days_with = len({s.day for s in data.sessions})
    print(f"저장: {out}")
    print(f"기록 {len(data.sessions)}개, 기록한 날 {days_with}일 (과목 {len(data.subjects)}개)")
    print(f"실행: python main.py --data {args.out}")


if __name__ == "__main__":
    main()
