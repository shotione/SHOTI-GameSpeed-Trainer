@echo off
setlocal
title DL1 Speed Trainer - Build and Deploy

set "VCVARS=C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
set "TRAINER_DIR=C:\Users\shotg\Desktop\DL Trainer"
set "GAME_DIR=D:\Dying Light - Platinum Edition"

echo.
echo Game folder : %GAME_DIR%
echo Trainer dir : %TRAINER_DIR%
echo.

echo [1/3] Copying winmm.dll to game folder as winmm_real.dll ...
copy /Y "%SystemRoot%\System32\winmm.dll" "%GAME_DIR%\winmm_real.dll"
if errorlevel 1 (
    echo ERROR: Copy failed. Are you running as Administrator?
    pause
    exit /b 1
)
echo OK

echo [2/3] Setting up MSVC ...
call "%VCVARS%" >nul 2>&1
if errorlevel 1 (
    echo ERROR: vcvars64.bat not found.
    pause
    exit /b 1
)

echo Compiling winmm_proxy.c ...
cd /d "%TRAINER_DIR%"
cl /nologo /LD /O2 /MD /wd4273 winmm_proxy.c /Fe:winmm.dll /link /DEF:winmm.def kernel32.lib user32.lib
if errorlevel 1 (
    echo ERROR: Compilation failed.
    pause
    exit /b 1
)
echo OK

echo [3/3] Deploying winmm.dll to game folder ...
copy /Y "%TRAINER_DIR%\winmm.dll" "%GAME_DIR%\winmm.dll"
if errorlevel 1 (
    echo ERROR: Deploy failed. Are you running as Administrator?
    pause
    exit /b 1
)
echo OK

echo.
echo BUILD COMPLETE
echo   1. Launch Dying Light via Steam
echo   2. Run dl1_trainer_v4.py
echo.
pause
