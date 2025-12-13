# 🚀 Getting Started with Ikonetu Django Backend

## What You Have

A **complete Django REST Framework backend** structure that replaces your Node.js backend. Here's what's ready:

### ✅ Complete & Ready to Use
- Django project configuration
- Custom User model with roles (founder/investor/admin)
- Session-based authentication (register, login, logout, me)
- Rate limiting on auth endpoints
- CORS configuration for frontend
- WebSocket infrastructure (Django Channels)
- All app directories created
- Database configuration
- Environment variable setup

### ⏳ Ready for Implementation
- Profile models (FounderProfile, InvestorProfile)
- Video management system
- Signal/interest system
- Matching & messaging
- Legal consent tracking
- Reporting system

## Prerequisites Checklist

Before you start, make sure you have:

- [ ] **Python 3.10+** installed
- [ ] **PostgreSQL 14+** installed and running
- [ ] **Redis** installed (for WebSocket support)
- [ ] **Git** installed
- [ ] **Node.js 18+** (for your React frontend)

### Check Your Prerequisites

```bash
# Check Python version (should be 3.10+)
python --version

# Check PostgreSQL (should be running)
psql --version

# Check Redis (should be installed)
redis-server --version

# Check Node.js (should be 18+)
node --version
```

## Step-by-Step Setup

### Step 1: Prepare PostgreSQL Database

```bash
# Start PostgreSQL service
# Windows (if installed as service):
# It should start automatically

# Mac:
brew services start postgresql@14

# Linux:
sudo systemctl start postgresql

# Create database
psql -U postgres
CREATE DATABASE ikonetu;
CREATE USER ikonetu_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ikonetu TO ikonetu_user;
\q
```

### Step 2: Set Up Backend

```bash
# Navigate to backend directory
cd C:\Users\samuel\Documents\ikonetu-backend

# Run setup script
# Windows:
setup.bat

# Mac/Linux:
chmod +x setup.sh
./setup.sh
```

The setup script will:
1. Create a virtual environment
2. Install all Python dependencies
3. Create `.env` file from template
4. Prompt you to configure environment variables

### Step 3: Configure Environment Variables

Edit the `.env` file that was created:

```env
# Database - IMPORTANT: Update with your PostgreSQL credentials
DATABASE_URL=postgresql://ikonetu_user:your_password@localhost:5432/ikonetu

# Django Security
SECRET_KEY=change-this-to-something-secure-and-random
DEBUG=True

# Hosts
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS - Your React frontend URLs
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5000

# Redis - For WebSocket support
REDIS_URL=redis://localhost:6379/0

# Session Configuration
SESSION_COOKIE_AGE=604800
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_SAMESITE=None
SESSION_COOKIE_HTTPONLY=True
```

**Important**: Generate a secure SECRET_KEY:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 4: Run Database Migrations

```bash
# Activate virtual environment first
# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

# Create and apply migrations
python manage.py makemigrations
python manage.py migrate
```

### Step 5: Create Admin User

```bash
python manage.py createsuperuser

# Follow the prompts:
# Email: admin@example.com
# Name: Admin User
# Password: (choose a strong password)
```

### Step 6: Test the Backend

```bash
# Start Django development server
python manage.py runserver 8000

# In another terminal, test the API:
curl http://localhost:8000/api/auth/me
# Should return: {"message": "Not authenticated"}
```

### Step 7: Start Redis (For WebSocket)

```bash
# Windows (if installed via Chocolatey):
redis-server

# Mac:
brew services start redis

# Linux:
redis-server

# Or using Docker:
docker run -d -p 6379:6379 redis:alpine
```

### Step 8: Update Your React Frontend

Update your frontend to point to the new Django backend:

**Option A: Update vite.config.ts (Recommended)**

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      }
    }
  }
})
```

**Option B: Update API calls directly**

```typescript
// client/src/lib/queryClient.ts
// Update the base URL in fetch calls to:
// http://localhost:8000/api/...
```

### Step 9: Run Everything Together

You'll need 3 terminals:

**Terminal 1: Django Backend**
```bash
cd C:\Users\samuel\Documents\ikonetu-backend
venv\Scripts\activate
python manage.py runserver 8000
```

**Terminal 2: Redis**
```bash
redis-server
```

**Terminal 3: React Frontend**
```bash
cd C:\Users\samuel\Documents\ikonetu
npm run dev
```

### Step 10: Test Authentication

Open your browser to `http://localhost:5173` (your React app) and:

1. Try registering a new user
2. Login with the user
3. Check if session persists after refresh

## What's Next?

Now that your backend is running, you need to implement the remaining features:

### Priority 1: Profile Models
1. Open `apps/profiles/models.py`
2. Implement `FounderProfile` and `InvestorProfile` models
3. Create serializers in `apps/profiles/serializers.py`
4. Implement views in `apps/profiles/views.py`
5. Configure URLs

### Priority 2: Video System
Same process for `apps/videos/`

### Priority 3: Signals & Matching
Implement `apps/signals/` and `apps/matches/`

### Priority 4: Complete the Rest
- Legal consent (`apps/legal/`)
- Reports (`apps/reports/`)

## Common Issues & Solutions

### Issue: Can't connect to PostgreSQL
**Solution**: 
- Check if PostgreSQL is running
- Verify `DATABASE_URL` in `.env`
- Test connection: `psql -U ikonetu_user -d ikonetu`

### Issue: Module import errors
**Solution**:
- Make sure virtual environment is activated
- Reinstall requirements: `pip install -r requirements.txt`

### Issue: CORS errors in browser
**Solution**:
- Check `CORS_ALLOWED_ORIGINS` in `.env`
- Make sure it includes your frontend URL
- Restart Django server after changing `.env`

### Issue: Session not persisting
**Solution**:
- Check cookie settings in browser DevTools
- Verify `SESSION_COOKIE_SECURE` and `SESSION_COOKIE_SAMESITE` in `.env`
- For development, try setting `SESSION_COOKIE_SECURE=False`

### Issue: Redis connection refused
**Solution**:
- Make sure Redis is running: `redis-cli ping` (should return PONG)
- Check `REDIS_URL` in `.env`

## Useful Commands Reference

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Run server
python manage.py runserver 8000

# Make migrations after model changes
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Django shell (for testing)
python manage.py shell

# Run tests
python manage.py test

# Collect static files (for production)
python manage.py collectstatic
```

## Project Structure

```
ikonetu-backend/
├── config/                 # Django settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/          # ✅ User auth (COMPLETE)
│   ├── profiles/          # ⏳ Profiles (TODO)
│   ├── videos/            # ⏳ Videos (TODO)
│   ├── signals/           # ⏳ Signals (TODO)
│   ├── matches/           # ⏳ Matches (TODO)
│   ├── legal/             # ⏳ Legal (TODO)
│   └── reports/           # ⏳ Reports (TODO)
├── manage.py
├── requirements.txt
├── .env
└── .env.example
```

## Additional Resources

- **SETUP_GUIDE.md** - Detailed technical setup
- **MIGRATION_CHECKLIST.md** - Track your progress
- **QUICK_REFERENCE.md** - Command quick reference
- **README.md** - Complete documentation

## Need Help?

1. Check the error message in the terminal
2. Look at `SETUP_GUIDE.md` for detailed troubleshooting
3. Review Django docs: https://docs.djangoproject.com/
4. Check DRF docs: https://www.django-rest-framework.org/

## Success Checklist

- [ ] PostgreSQL database created and running
- [ ] Virtual environment created and activated
- [ ] Dependencies installed
- [ ] `.env` configured with correct database URL
- [ ] Migrations applied successfully
- [ ] Admin user created
- [ ] Django server runs on port 8000
- [ ] Redis running (if using WebSocket)
- [ ] Frontend can reach backend API
- [ ] Registration/login working

Once all checkboxes are checked, you're ready to start implementing the remaining models!

---

**You're all set! Start with implementing the profile models and work your way through the checklist.**