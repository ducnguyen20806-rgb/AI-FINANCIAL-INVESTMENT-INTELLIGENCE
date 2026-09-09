@echo off
chcp 65001 > nul
title AI Financial & Investment Intelligence Platform

echo ========================================================================
echo   AI FINANCIAL PLATFORM — KHOI DONG HE THONG TRONG 1 LENH
echo ========================================================================
echo.

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
) else (
    set "PYTHON_CMD=python"
)

%PYTHON_CMD% run.py %*
pause

