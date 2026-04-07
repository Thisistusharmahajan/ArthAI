@echo off
echo ============================================
echo  ArthaAI - Windows Setup Script
echo ============================================
echo.

:: Step 1: Upgrade pip and core build tools FIRST (fixes pkg_resources error)
echo [1/5] Upgrading pip, setuptools, wheel...
python.exe -m pip install --upgrade pip setuptools wheel
if %errorlevel% neq 0 (
    echo ERROR: Failed to upgrade pip. Make sure Python is installed correctly.
    pause
    exit /b 1
)
echo Done.
echo.

:: Step 2: Create virtual environment
echo [2/5] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
) else (
    echo venv already exists, skipping.
)
echo Done.
echo.

:: Step 3: Activate venv
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
echo Done.
echo.

:: Step 4: Upgrade pip INSIDE venv too
echo [4/5] Upgrading pip inside venv...
python.exe -m pip install --upgrade pip setuptools wheel
echo Done.
echo.

:: Step 5: Install core requirements
echo [5/5] Installing core requirements...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Some packages failed. Try running manually:
    echo   pip install flask flask-cors flask-jwt-extended anthropic python-dotenv
    echo   pip install faiss-cpu sentence-transformers numpy pandas
    echo   pip install PyPDF2 pdfplumber openpyxl requests beautifulsoup4
    echo   pip install gTTS reportlab apscheduler
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Setup complete!
echo ============================================
echo.
echo Next steps:
echo   1. Copy .env.example to .env
echo   2. Add your ANTHROPIC_API_KEY to .env
echo   3. Run: python app.py
echo.
pause
