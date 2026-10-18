@echo off
if "%~1"=="" (
    echo Usage: study.cmd path\to\notes.md [question-count]
    exit /b 1
)
if "%~2"=="" (
    py mini_llm.py --study "%~1"
) else (
    py mini_llm.py --study "%~1" --questions "%~2"
)
