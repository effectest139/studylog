@echo off
chcp 65001 >nul
rem StudyLog 시연용: 가짜 데이터 data\dev.json 으로 연다. 실제 데이터는 건드리지 않는다.
rem 어디서 더블클릭하든(바로가기 포함) 이 파일이 있는 폴더를 기준으로 동작한다.
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo 가상환경 .venv 가 없어요. 프로젝트 폴더에서 아래 명령을 먼저 실행해 주세요.
    echo     python -m venv .venv
    echo     .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)
if not exist "data\dev.json" (
    echo 가짜 데이터를 만드는 중이에요...
    rem 오류 출력은 임시 파일에 받아 두고, 실패했을 때만 logs\error.log 에 옮긴다
    ".venv\Scripts\python.exe" tools\make_fake_data.py >nul 2>"%TEMP%\studylog_fake.err"
    if errorlevel 1 (
        if not exist "logs" mkdir "logs"
        type "%TEMP%\studylog_fake.err" >>"logs\error.log"
        echo 가짜 데이터를 만들지 못했어요. logs\error.log 를 확인해 주세요.
        pause
        exit /b 1
    )
)
start "" ".venv\Scripts\pythonw.exe" main.py --data data\dev.json
