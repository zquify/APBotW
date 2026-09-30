@echo off
setlocal

title WiiXLaunch BotW - Build, Deploy and Launch

set "WX=C:\Projects\WiiXLaunch"
set "BOTW=C:\Projects\wiixlaunch-botw"
set "CEMU=C:\Cemu\cemu_1.26.2"
set "HOST_SOURCE=%WX%\build\host"
set "HOST_DEST=%CEMU%\graphicPacks\WiiXLaunch_BotW"
set "MOD_SOURCE=%WX%\mods\botw_ap_bridge"

echo.
echo ==========================================
echo   WiiXLaunch BotW Build and Launch
echo ==========================================
echo.

if not exist "%WX%\build_cemu.bat" (
    echo ERROR: WiiXLaunch build script not found.
    pause
    exit /b 1
)

if not exist "%MOD_SOURCE%\mod.json" (
    echo ERROR: BotW bridge source not found.
    echo Expected: %MOD_SOURCE%
    pause
    exit /b 1
)

if not exist "%CEMU%\Cemu.exe" (
    echo ERROR: Cemu.exe not found.
    echo Expected: %CEMU%\Cemu.exe
    pause
    exit /b 1
)

echo [1/5] Building WiiXLaunch Cemu host...
pushd "%WX%"
call build_cemu.bat
if errorlevel 1 (
    echo ERROR: WiiXLaunch host build failed.
    popd
    pause
    exit /b 1
)
popd

if not exist "%HOST_SOURCE%" (
    echo ERROR: Host build output not found:
    echo %HOST_SOURCE%
    pause
    exit /b 1
)

echo.
echo [2/5] Deploying BotW graphic pack...
pushd "%WX%"
python scripts\deploy.py --target botw
if errorlevel 1 (
    echo ERROR: Graphic pack deployment failed.
    popd
    pause
    exit /b 1
)

echo.
echo [3/5] Regenerating host SDK...
python scripts\make_sdk.py --host
if errorlevel 1 (
    echo ERROR: Host SDK generation failed.
    popd
    pause
    exit /b 1
)
popd

echo.
echo [4/5] Building the BotW Archipelago bridge...
python "%WX%\sdk\scripts\build_mod.py" ^
  --source "%MOD_SOURCE%" ^
  --id botw_ap_bridge ^
  --target cemu ^
  --wiixlaunch "%WX%" ^
  --include "%BOTW%\include"

if errorlevel 1 (
    echo ERROR: Bridge module build failed.
    pause
    exit /b 1
)

if not exist "%WX%\build\botw_ap_bridge.wxlm" (
    echo ERROR: Built bridge module not found.
    pause
    exit /b 1
)

echo.
echo Copying host files into Cemu...
if not exist "%HOST_DEST%" mkdir "%HOST_DEST%"

robocopy "%HOST_SOURCE%" "%HOST_DEST%" /E
if errorlevel 8 (
    echo ERROR: Copying host files into Cemu failed.
    pause
    exit /b 1
)

echo.
echo Installing the freshly built bridge module...
set "MOD_DEST=%HOST_DEST%\content\WiiXLaunch\mods"
if not exist "%MOD_DEST%" mkdir "%MOD_DEST%"

copy /Y "%WX%\build\botw_ap_bridge.wxlm" "%MOD_DEST%\botw_ap_bridge.wxlm"
if errorlevel 1 (
    echo ERROR: Installing the bridge module failed.
    pause
    exit /b 1
)

echo.
echo [5/5] Launching Cemu...
start "" "%CEMU%\Cemu.exe"

echo.
echo ==========================================
echo   Build and deployment completed!
echo ==========================================
echo.
echo Cemu has been launched.
echo Load Breath of the Wild and enable the
echo WiiXLaunch graphic pack if it is not enabled.
echo.
echo Bridge address: 127.0.0.1:8080
echo.
pause
endlocal