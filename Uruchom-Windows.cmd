@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 Uruchom.py
) else (
    python Uruchom.py
)
if errorlevel 1 (
    echo Nie udało się uruchomić. Zainstaluj Python 3.11 lub nowszy z python.org i zaznacz Add Python to PATH.
    pause
)
