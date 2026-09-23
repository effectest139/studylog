from datetime import date, datetime

from studylog.core import colors, fmt


def test_tint_matches_design():
    # 디자인과 같은 반올림(0.5 올림)을 쓰는지 확인: G 236.5 → 237(ED)
    assert colors.tint("#4F46E5") == "#EDEDFC"


def test_dark_has_enough_contrast():
    for c in colors.PALETTE:
        assert colors.contrast_ratio(colors.dark(c), colors.tint(c)) >= 4.5


def test_next_unused():
    assert colors.next_unused([]) == colors.PALETTE[0]
    assert colors.next_unused(["#4f46e5", "#0EA5E9"]) == colors.PALETTE[2]
    assert colors.next_unused(list(colors.PALETTE)) == colors.PALETTE[0]


def test_duration():
    assert fmt.duration(85 * 60) == "1시간 25분"
    assert fmt.duration(3600) == "1시간"
    assert fmt.duration(13 * 60 + 59) == "13분"
    assert fmt.duration(0) == "0분"
    assert fmt.duration(0, empty="0시간 0분") == "0시간 0분"


def test_duration_hms_and_clock():
    assert fmt.duration_hms(4365) == "1시간 12분 45초"
    assert fmt.duration_hms(45) == "45초"
    assert fmt.clock(4365) == "01:12:45"
    assert fmt.duration_short(90 * 60) == "1h 30m"


def test_time_of_day():
    assert fmt.time_of_day(datetime(2026, 9, 23, 19, 30)) == "오후 7:30"
    assert fmt.time_of_day(datetime(2026, 9, 23, 0, 5)) == "오전 12:05"
    assert fmt.time_of_day(datetime(2026, 9, 23, 12, 0)) == "오후 12:00"


def test_dates():
    d = date(2026, 9, 23)
    assert fmt.date_long(d) == "2026년 9월 23일 수요일"
    assert fmt.date_short(d, today=d) == "9월 23일 (수) · 오늘"
    assert fmt.date_range(date(2026, 9, 21), date(2026, 9, 27)) == "9월 21일 – 9월 27일"
