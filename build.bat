@echo off
setlocal
cd /d "%~dp0"

if not exist "venv\" (
    echo Venv not found. Run launch.bat first to set up the environment.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo Installing PyInstaller and build deps...
pip install pyinstaller pywin32 --quiet --disable-pip-version-check

echo.
echo Cleaning previous build artefacts...
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

echo.
echo Building sftp-sync-panel.exe...
echo.

pyinstaller --noconfirm "sftp-sync-panel.spec"

if errorlevel 1 (
    echo.
    echo Build failed. See above for errors.
    pause
    exit /b 1
)

echo.
echo =====================================================
echo  Build complete: dist\sftp-sync-panel\
echo  Run: dist\sftp-sync-panel\sftp-sync-panel.exe
echo  Copy the dist\sftp-sync-panel\ folder to deploy.
echo =====================================================
echo.
pause
endlocal
