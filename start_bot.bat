@echo off

cd /d "%~dp0"

:loop

python bot.py

timeout /t 2

goto loop
