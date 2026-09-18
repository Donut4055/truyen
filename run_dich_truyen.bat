@echo off
chcp 65001 > nul
title AI Story Translator - Tool Dich Truyen Chuyen Nghiep
echo ========================================================
echo   KHOI DONG TOOL DICH TRUYEN AI (VAN PHONG CHUAN CHI)
echo ========================================================
cd /d "%~dp0"
python cli.py
pause
