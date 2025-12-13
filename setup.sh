#!/bin/bash

echo "================================"
echo "Ikonetu Django Backend Setup"
echo "================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

echo "[1/7] Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi

echo "[2/7] Activating virtual environment..."
source venv/bin/activate

echo "[3/7] Upgrading pip..."
pip install --upgrade pip

echo "[4/7] Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo "[5/7] Creating .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ".env file created! Please edit it with your database credentials."
    read -p "Press enter after editing .env file..."
else
    echo ".env file already exists, skipping..."
fi

echo "[6/7] Running database migrations..."
python manage.py makemigrations
python manage.py migrate

echo "[7/7] Setup complete!"
echo ""
echo "================================"
echo "Next Steps:"
echo "================================"
echo "1. Make sure PostgreSQL is running"
echo "2. Make sure Redis is running (for WebSocket)"
echo "3. Create a superuser: python manage.py createsuperuser"
echo "4. Run the server: python manage.py runserver 8000"
echo "5. Update frontend to point to http://localhost:8000"
echo ""
echo "To start the server now, run:"
echo "  python manage.py runserver 8000"
echo ""