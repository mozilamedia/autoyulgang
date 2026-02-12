@echo off
REM Build script for Window Auto Tool
REM This script must be run as Administrator

echo ========================================
echo Window Auto Tool - Build Script
echo ========================================
echo.


REM Check if PyInstaller is installed
python -m pip show pyinstaller >nul 2>&1
if %errorLevel% neq 0 (
    echo PyInstaller not found. Installing...
    python -m pip install pyinstaller
    if %errorLevel% neq 0 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
)

echo Building window_auto_tool.exe...
echo This executable will ALWAYS require Administrator privileges
echo.

REM Build the executable with admin manifest
pyinstaller --onefile --windowed --icon=NONE ^
    --name=WindowAutoTool ^
    --manifest=app.manifest ^
    --add-data "templates;templates" ^
    --hidden-import=PIL ^
    --hidden-import=cv2 ^
    --hidden-import=numpy ^
    --hidden-import=pyautogui ^
    --hidden-import=pygetwindow ^
    --hidden-import=win32gui ^
    --hidden-import=win32con ^
    --hidden-import=win32api ^
    window_auto_tool.py

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo Build completed successfully!
    echo ========================================
    echo.
    echo Executable location: dist\WindowAutoTool.exe
    echo.
    echo IMPORTANT NOTES:
    echo   - This .exe will ALWAYS require Administrator privileges
    echo   - Windows will show UAC prompt when you run it
    echo   - Copy the following to the same folder as the .exe:
    echo     * templates folder
    echo     * script.json (if using script mode)
    echo.
) else (
    echo.
    echo ========================================
    echo Build FAILED!
    echo ========================================
    echo.
)

pause
