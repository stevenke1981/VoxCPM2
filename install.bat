@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1

echo.
echo  ================================================================
echo   VoxCPM2 Studio  --  Installation Script
echo   powered by openbmb/VoxCPM2
echo  ================================================================
echo.
echo  This script will:
echo    1. Install the uv package manager
echo    2. Create a Python virtual environment (.venv)
echo    3. Install all dependencies
echo    4. Install CUDA-enabled PyTorch (if NVIDIA GPU detected)
echo    5. Run a smoke test to verify the installation
echo    6. Create a desktop shortcut
echo.
echo  Internet connection is required.
echo  First install may download up to 15 GB.
echo.
pause

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM ── 1. Check Windows version ─────────────────────────────────────────────────
echo "[INSTALL] Checking system..."
ver | findstr /i "10\." >nul 2>&1
if errorlevel 1 (
    ver | findstr /i "11\." >nul 2>&1
)
echo "[INFO]    OS: Windows %OS%"

REM ── 2. Check disk space (need at least 20 GB free) ───────────────────────────
for /f "tokens=3" %%a in ('dir /-c "%SCRIPT_DIR%" 2^>nul ^| findstr /i "bytes free"') do set FREE_BYTES=%%a
echo "[INFO]    Install directory: %SCRIPT_DIR%"

REM ── 3. Install / update uv ───────────────────────────────────────────────────
echo.
echo "[INSTALL] Step 1/5 -- Checking uv package manager..."
where uv >nul 2>&1
if errorlevel 1 (
    echo "[INSTALL] uv not found. Downloading and installing..."
    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if errorlevel 1 (
        echo "[ERROR]   uv installation failed."
        echo "          Please install manually: https://docs.astral.sh/uv/"
        goto :fail
    )
    echo "[OK]      uv installed."
    REM Refresh PATH so uv is accessible in this session
    set "PATH=%USERPROFILE%\.cargo\bin;%LOCALAPPDATA%\uv\bin;%PATH%"
) else (
    echo "[OK]      uv already installed."
)

for /f "tokens=*" %%v in ('uv --version 2^>^&1') do set UV_VER=%%v
echo "[INFO]    %UV_VER%"

REM ── 4. Create virtual environment ────────────────────────────────────────────
echo.
echo "[INSTALL] Step 2/5 -- Creating virtual environment..."
if exist ".venv\" (
    echo "[INFO]    Existing .venv found -- will reuse."
) else (
    echo "[INFO]    Creating .venv with Python 3.10+..."
    uv venv --python 3.10
    if errorlevel 1 (
        echo "[WARN]    Python 3.10 not found via uv. Trying with system Python..."
        uv venv
        if errorlevel 1 (
            echo "[ERROR]   Could not create virtual environment."
            echo "          Install Python 3.10+ from https://www.python.org/"
            goto :fail
        )
    )
    echo "[OK]      Virtual environment created at .venv\"
)

REM ── 5. Install all dependencies ───────────────────────────────────────────────
echo.
echo "[INSTALL] Step 3/5 -- Installing dependencies (this may take several minutes)..."
echo "[INFO]    Packages include: voxcpm, customtkinter, sounddevice, deep-translator, etc."
uv sync
if errorlevel 1 (
    echo "[ERROR]   Dependency installation failed."
    echo "          Check your internet connection and re-run install.bat"
    goto :fail
)
echo "[OK]      Base dependencies installed."

REM ── 6. GPU detection and CUDA PyTorch ─────────────────────────────────────────
echo.
echo "[INSTALL] Step 4/5 -- Checking GPU / PyTorch CUDA support..."
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo "[INFO]    No NVIDIA GPU detected -- using CPU mode."
    echo "[INFO]    CPU inference will be slower but fully functional."
    goto :after_gpu
)

REM NVIDIA GPU found
for /f "tokens=*" %%g in ('nvidia-smi --query-gpu=name --format=csv^,noheader 2^>nul') do set GPU_NAME=%%g
echo "[INFO]    GPU detected: !GPU_NAME!"

REM Check if torch CUDA is already working
uv run python -c "import torch; exit(0 if torch.cuda.is_available() else 1)" >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%v in ('uv run python -c "import torch; print(torch.__version__)" 2^>nul') do set TORCH_VER=%%v
    echo "[OK]      PyTorch !TORCH_VER! with CUDA already installed."
    goto :after_gpu
)

echo "[INSTALL] Installing CUDA 12.4 PyTorch (approx. 2-3 GB download)..."
echo "[INFO]    Please wait -- this is a one-time download."
uv pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124 --force-reinstall
if errorlevel 1 (
    echo "[WARN]    CUDA PyTorch install failed."
    echo "          App will fall back to CPU mode."
    goto :after_gpu
)

for /f "tokens=*" %%v in ('uv run python -c "import torch; print(torch.__version__)" 2^>nul') do set TORCH_VER=%%v
echo "[OK]      PyTorch !TORCH_VER! with CUDA installed."

:after_gpu

REM ── 7. Smoke test ─────────────────────────────────────────────────────────────
echo.
echo "[INSTALL] Step 5/5 -- Running smoke test..."

uv run python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo "[ERROR]   customtkinter import failed."
    goto :fail
)
echo "[OK]      customtkinter  OK"

uv run python -c "import torch" >nul 2>&1
if errorlevel 1 (
    echo "[ERROR]   torch import failed."
    goto :fail
)
for /f "tokens=*" %%v in ('uv run python -c "import torch; print(torch.__version__)" 2^>nul') do set TORCH_VER=%%v
echo "[OK]      torch !TORCH_VER!  OK"

uv run python -c "import voxcpm" >nul 2>&1
if errorlevel 1 (
    echo "[ERROR]   voxcpm import failed."
    goto :fail
)
echo "[OK]      voxcpm  OK"

uv run python -c "import soundfile, sounddevice, numpy" >nul 2>&1
if errorlevel 1 (
    echo "[ERROR]   Audio libraries import failed."
    goto :fail
)
echo "[OK]      soundfile / sounddevice / numpy  OK"

uv run python -c "from deep_translator import GoogleTranslator" >nul 2>&1
if errorlevel 1 (
    echo "[ERROR]   deep-translator import failed."
    goto :fail
)
echo "[OK]      deep-translator  OK"

REM ── 8. Create desktop shortcut ────────────────────────────────────────────────
echo.
echo "[INSTALL] Creating desktop shortcut..."
set "SHORTCUT=%USERPROFILE%\Desktop\VoxCPM2 Studio.lnk"
set "TARGET=%SCRIPT_DIR%start.bat"
set "ICON=%SCRIPT_DIR%start.bat"

powershell -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $sc = $ws.CreateShortcut('%SHORTCUT%'); ^
   $sc.TargetPath = '%TARGET%'; ^
   $sc.WorkingDirectory = '%SCRIPT_DIR%'; ^
   $sc.WindowStyle = 1; ^
   $sc.Description = 'VoxCPM2 Studio TTS Application'; ^
   $sc.Save()" >nul 2>&1

if exist "%SHORTCUT%" (
    echo "[OK]      Desktop shortcut created: VoxCPM2 Studio.lnk"
) else (
    echo "[INFO]    Could not create desktop shortcut (permission issue -- safe to ignore)."
)

REM ── Done ──────────────────────────────────────────────────────────────────────
echo.
echo  ================================================================
echo   Installation complete!
echo  ================================================================
echo.
echo   To start the application:
echo     Double-click  "VoxCPM2 Studio"  on your Desktop
echo     OR run  start.bat  in this folder
echo.
echo   First launch:  go to Settings and click "Load Model"
echo   The model (~8 GB) will download on first use.
echo.
echo   For GPU acceleration, make sure CUDA drivers are up to date:
echo   https://www.nvidia.com/drivers
echo.
pause
exit /b 0

:fail
echo.
echo  ================================================================
echo   [ERROR] Installation failed.
echo  ================================================================
echo.
echo   Please check the error messages above and re-run install.bat
echo   after resolving the issue.
echo.
echo   Common fixes:
echo     - Ensure you have internet access
echo     - Run install.bat as Administrator if permission errors occur
echo     - Install Python 3.10+ from https://www.python.org/
echo.
pause
exit /b 1
