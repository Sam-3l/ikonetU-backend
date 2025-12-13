# Ikonetu Backend - Quick Reference

## 🚀 Getting Started

### First Time Setup
```bash
# Windows
setup.bat

# Mac/Linux
chmod +x setup.sh && ./setup.sh
```

### Daily Development
```bash
# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Run server
python manage.py runserver 8000
```

## 📁 Project Structure

```
ikonetu-backend/
├── config/              # Django settings
├── apps/
│   ├── accounts/       # ✅ Auth (DONE)
│   ├── profiles/       # ⏳ Profiles (TODO)
│   ├── videos/         # ⏳ Videos (TODO)
│   ├── signals/        # ⏳ Signals (TODO)
│   ├── matches/        # ⏳ Matches (TODO)
│   ├── legal/          # ⏳ Legal (TODO)
│   └── reports/        # ⏳ Reports (TODO)
└── manage.py
```

## 🔧 Common Commands

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver 8000

# Run tests
python manage.py test

# Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic
```

## 🌐 API Endpoints (Port 8000)

### Auth
- POST `/api/auth/register`
- POST `/api/auth/login`
- POST `/api/auth/logout`
- GET `/api/auth/me`

### Profiles
- GET/PUT `/api/founder/profile`
- GET/PUT `/api/investor/profile`

### Videos
- GET `/api/videos/feed`
- GET `/api/videos/my`
- POST `/api/videos`

### Signals
- POST `/api/signals`
- GET `/api/signals/received`
- GET `/api/signals/sent`

### Matches
- GET `/api/matches`
- POST `/api/matches/:id/accept`
- GET/POST `/api/matches/:id/messages`

### Admin
- GET `/api/admin/users`
- GET `/api/admin/videos`
- GET `/api/admin/reports`

## 🔐 Environment Variables

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/ikonetu
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5000
```

## 🔨 Next Steps

1. **Implement Models** - Each app needs models.py completed
2. **Create Serializers** - Add serializers.py for each model
3. **Build Views** - Implement views.py endpoints
4. **Configure URLs** - Set up urls.py routing
5. **Test Frontend** - Connect React frontend to Django

## 📚 Important Files

- `SETUP_GUIDE.md` - Detailed setup instructions
- `MIGRATION_CHECKLIST.md` - Migration progress tracker
- `README.md` - Full documentation
- `.env.example` - Environment variable template

## 🆘 Troubleshooting

### Can't connect to database
Check `DATABASE_URL` in `.env`

### CORS errors
Update `CORS_ALLOWED_ORIGINS` in `.env`

### Migrations not applying
```bash
python manage.py migrate --run-syncdb
```

### Port already in use
Change port: `python manage.py runserver 8001`

## 📞 Support

See detailed docs:
- SETUP_GUIDE.md
- MIGRATION_CHECKLIST.md
- README.md