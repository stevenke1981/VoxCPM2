@echo off
setlocal EnableDelayedExpansion

echo.
echo  ============================================================
echo   VoxCPM2 Studio  ^|  powered by openbmb/VoxCPM2
echo  ============================================================
echo.

REM ── 1. 檢查 uv ──────────────────────────────────────────────────────────────
where uv >nul 2>&1
if errorlevel 1 (
    echo [SETUP] uv 未安裝，正在自動安裝...
    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if errorlevel 1 (
        echo [ERROR] uv 安裝失敗，請手動安裝：https://docs.astral.sh/uv/
        goto :fail
    )
    echo [SETUP] uv 安裝完成，請重新執行此腳本。
    pause
    exit /b 0
)

for /f "tokens=*" %%v in ('uv --version 2^>^&1') do set UV_VER=%%v
echo [INFO]  %UV_VER%

REM ── 2. 建立 / 重用虛擬環境 .venv ────────────────────────────────────────────
if not exist ".venv\" (
    echo [SETUP] 建立虛擬環境 .venv  ^(Python 3.10+^)...
    uv venv --python 3.10
    if errorlevel 1 (
        echo [WARN]  Python 3.10 未找到，嘗試使用系統預設 Python...
        uv venv
        if errorlevel 1 (
            echo [ERROR] 建立虛擬環境失敗。請確認已安裝 Python 3.10+
            goto :fail
        )
    )
    echo [SETUP] 虛擬環境建立完成。
) else (
    echo [INFO]  使用現有虛擬環境 .venv
)

REM ── 3. 同步依賴 ─────────────────────────────────────────────────────────────
echo [SETUP] 同步依賴套件 ^(首次執行需較長時間，請耐心等候^)...
uv sync
if errorlevel 1 (
    echo [WARN]  uv sync 失敗，嘗試 uv pip install...
    uv pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] 依賴安裝失敗。
        goto :fail
    )
)

echo.
echo [INFO]  所有依賴已就緒。
echo.

REM ── 4. 啟動應用程式 ─────────────────────────────────────────────────────────
echo [INFO]  啟動 VoxCPM2 Studio...
echo  ------------------------------------------------------------
uv run python main.py
set APP_EXIT=%ERRORLEVEL%

echo.
if %APP_EXIT% neq 0 (
    echo [WARN]  應用程式以代碼 %APP_EXIT% 退出。
    pause
)
goto :eof

:fail
echo.
echo [ERROR] 啟動失敗，請查閱上方錯誤訊息。
pause
exit /b 1
