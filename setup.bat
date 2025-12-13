@echo off
echo ================================
echo Ikonetu Django Backend Setup
echo ================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher from python.org
    pause
    exit /b 1
)

echo [1/7] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/7] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/7] Upgrading pip...
python -m pip install --upgrade pip

echo [4/7] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [5/7] Creating .env file...
if not exist .env (
    copy .env.example .env
    echo .env file created! Please edit it with your database credentials.
    echo Press any key after editing .env file...
    pause
) else (
    echo .env file already exists, skipping...
)

echo [6/7] Running database migrations...
python manage.py makemigrations
python manage.py migrate

echo [7/7] Setup complete!
echo.
echo ================================
echo Next Steps:
echo ================================
echo 1. Make sure PostgreSQL is running
echo 2. Make sure Redis is running (for WebSocket)
echo 3. Create a superuser: python manage.py createsuperuser
echo 4. Run the server: python manage.py runserver 8000
echo 5. Update frontend to point to http://localhost:8000
echo.
echo To start the server now, run:
echo   python manage.py runserver 8000
echo.
pause