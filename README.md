# StudyLog

과목별 공부 시간을 기록하고, 주간·월간으로 돌아보는 Windows 데스크톱 앱입니다.
Python과 CustomTkinter로 만들었고, 그래프는 matplotlib로 그립니다.

## 주요 기능

- **과목 카드로 바로 시작**: 홈에서 과목 카드를 누르면 타이머가 시작됩니다. Space로 일시정지·재개하고, 일시정지한 시간은 공부 시간에서 빠집니다.
- **기록**: 날짜별 공부 기록과 하루 합계를 보여 줍니다. 기록을 하나씩 삭제할 수 있습니다.
- **분석**: 요일별·주차별 막대 그래프, 과목별 비율 도넛, 지난주·지난달 같은 기간과의 비교를 보여 줍니다. 기록한 날이 3일 이상이면 학습 조언도 나옵니다.
- **목표**: 주간 전체 목표와 과목별 주간 목표를 정하고 달성률을 확인합니다.
- **연속 공부일**: 하루 1분 이상 공부한 날이 며칠째 이어지는지 보여 줍니다.

과목은 최대 10개까지 만들 수 있고, 1분 미만의 기록은 저장되지 않습니다.

## 실행 환경

- Windows 10/11 (글꼴: 맑은 고딕, 타이머: Consolas)
- Python 3.10 이상 (3.14에서 확인)

## 설치와 실행

```bash
git clone https://github.com/effectest139/studylog.git
cd studylog
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

콘솔 창 없이 실행하려면 `pythonw main.py`를 쓰세요. 이때 오류는 `logs/error.log`에 기록됩니다.

## 데이터

- 기록은 `data/studylog.json`에 저장됩니다. 이 폴더는 git에서 제외되어 있습니다.
- 다른 파일을 쓰려면 `python main.py --data 경로.json`으로 실행합니다.
- 파일이 깨져서 읽을 수 없으면 원래 파일을 `.corrupt-날짜.json`으로 옮겨 두고 새로 시작합니다.
- 프로필의 **데이터 초기화**는 지금 연 파일만 비웁니다.

## 개발

```bash
pytest                                   # 계산·저장 코드 테스트
python tools/make_fake_data.py           # 가짜 기록 data/dev.json 만들기 (최근 70일)
python main.py --data data/dev.json      # 가짜 기록으로 실행
```

`tools/make_fake_data.py`는 실제 데이터 파일(`data/studylog.json`)에는 쓰지 않습니다.

### 구조

```
main.py                 진입점 (--data 옵션)
studylog/core/          데이터·계산 (tkinter를 쓰지 않아 창 없이 테스트할 수 있음)
  models.py             과목·기록 데이터 구조
  storage.py            JSON 읽기·쓰기 (임시 파일에 쓴 뒤 바꿔치기)
  store.py              과목·기록·목표 관리와 입력 검사
  stats.py              합계·연속일·주간/월간·비교
  advice.py             학습 조언
  greeting.py           홈 인사말
  timer.py, fmt.py, colors.py
studylog/ui/            화면 (CustomTkinter, matplotlib)
  pages/                홈·공부·기록·분석·목표·처음 등록
  dialogs/              과목·목표·프로필·확인 대화상자
  widgets/              공통 위젯(과목 카드, 사이드바, 끌어서 스크롤 등)
tests/                  pytest
tools/                  개발용 도구
```

## 라이선스

[MIT](LICENSE)
