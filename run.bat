@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if exist "%~dp0.venv\Scripts\python.exe" set "PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=python"

"%PYTHON%" -c "import customtkinter, PIL, pymupdf, tkinterdnd2" >nul 2>nul
if errorlevel 1 (
    echo.
    echo Не удалось запустить приложение: не установлены зависимости.
    echo Выполните команду: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

set "PYTHONW=%PYTHON:python.exe=pythonw.exe%"
start "" "%PYTHONW%" app.py
