@echo off
chcp 65001 >nul
rem StudyLog 실행: 실제 데이터 data\studylog.json 으로 연다.
rem 어디서 더블클릭하든(바로가기 포함) 이 파일이 있는 폴더를 기준으로 동작한다.
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo 가상환경 .venv 가 없어요. 프로젝트 폴더에서 아래 명령을 먼저 실행해 주세요.
    echo     python -m venv .venv
    echo     .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)
rem pythonw는 검은 명령 창 없이 실행한다. 오류는 logs\error.log 에 남는다.
start "" ".venv\Scripts\pythonw.exe" main.py
