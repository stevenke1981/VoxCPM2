@echo off
setlocal EnableDelayedExpansion

echo.
echo  ============================================================
echo   VoxCPM2 Studio  ^|  powered by openbmb/VoxCPM2
echo  ============================================================
echo.

REM ── 1. Check for uv ─────────────────────────────────────────────────────────
where uv >nul 2>&1
if errorlevel 1 (
    echo "[SETUP] uv not found. Installing automatically..."
    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if errorlevel 1 (
        echo "[ERROR] uv installation failed."
        echo "        Please install manually: https://docs.astral.sh/uv/"
        goto :fail
    )
    echo "[SETUP] uv installed. Please re-run this script."
    pause
    exit /b 0
)

for /f "tokens=*" %%v in ('uv --version 2^>^&1') do set UV_VER=%%v
echo "[INFO]  %UV_VER%"

REM ── 2. Create / reuse virtual environment ───────────────────────────────────
if not exist ".venv\" (
    echo "[SETUP] Creating virtual environment .venv  (Python 3.10+)..."
    uv venv --python 3.10
    if errorlevel 1 (
        echo "[WARN]  Python 3.10 not found. Trying system default Python..."
        uv venv
        if errorlevel 1 (
            echo "[ERROR] Failed to create virtual environment."
            echo "        Please install Python 3.10 or later."
            goto :fail
        )
    )
    echo "[SETUP] Virtual environment created."
) else (
    echo "[INFO]  Using existing virtual environment .venv"
)

REM ── 3. Sync dependencies ────────────────────────────────────────────────────
echo "[SETUP] Syncing dependencies (first run may take a while)..."
uv sync
if errorlevel 1 (
    echo "[WARN]  uv sync failed. Falling back to uv pip install..."
    uv pip install -r requirements.txt
    if errorlevel 1 (
        echo "[ERROR] Dependency installation failed."
        goto :fail
    )
)

REM ── 4. GPU check — reinstall CUDA PyTorch if needed ─────────────────────────
nvidia-smi >nul 2>&1
if not errorlevel 1 (
    echo "[INFO]  NVIDIA GPU detected. Checking PyTorch CUDA support..."
    uv run python -c "import torch; exit(0 if torch.cuda.is_available() else 1)" >nul 2>&1
    if errorlevel 1 (
        echo "[INFO]  PyTorch is CPU-only. Installing CUDA 12.4 build..."
        echo "[INFO]  (This is a one-time ~2 GB download — please wait)"
        uv pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124 --force-reinstall
        if errorlevel 1 (
            echo "[WARN]  CUDA PyTorch install failed. Continuing with CPU fallback."
        ) else (
            echo "[INFO]  CUDA PyTorch installed successfully."
        )
    ) else (
        for /f "tokens=*" %%g in ('uv run python -c "import torch; print(torch.cuda.get_device_name(0))" 2^>nul') do set GPU_NAME=%%g
        echo "[INFO]  GPU acceleration ready  --  !GPU_NAME!"
    )
) else (
    echo "[INFO]  No NVIDIA GPU detected. Running on CPU."
)

echo.
echo "[INFO]  All dependencies ready."
echo.

REM ── 5. Launch application ───────────────────────────────────────────────────
echo "[INFO]  Launching VoxCPM2 Studio..."
echo  ------------------------------------------------------------
uv run python main.py
set APP_EXIT=%ERRORLEVEL%

echo.
if %APP_EXIT% neq 0 (
    echo "[WARN]  Application exited with code %APP_EXIT%."
    pause
)
goto :eof

:fail
echo.
echo "[ERROR] Startup failed. Please check the messages above."
pause
exit /b 1
