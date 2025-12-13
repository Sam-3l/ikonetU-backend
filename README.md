# Ikonetu Django REST Framework Backend

A complete Django REST Framework backend replacement for the Node.js/Express backend, maintaining full API compatibility with the existing React frontend.

## 🚀 Quick Start

### Windows
```bash
# Run the setup script
setup.bat

# After setup completes:
python manage.py createsuperuser
python manage.py runserver 8000
```

### macOS/Linux
```bash
# Make setup script executable and run
chmod +x setup.sh
./setup.sh

# After setup completes:
python manage.py createsuperuser
python manage.py runserver 8000
```

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis (for WebSocket functionality)

## 🏗️ Project Structure

```
ikonetu-backend/
├── config/                     # Django project configuration
│   ├── settings.py            # Main settings
│   ├── urls.py                # Root URL configuration
│   ├── wsgi.py                # WSGI application
│   ├── asgi.py                # ASGI for WebSocket
│   └── exceptions.py          # Custom exception handlers
│
├── apps/
│   ├── accounts/              # User authentication & management
│   │   ├── models.py          # Custom User model
│   │   ├── views.py           # Auth endpoints
│   │   ├── serializers.py     # User serializers
│   │   ├── authentication.py  # Custom session auth
│   │   └── middleware.py      # Rate limiting
│   │
│   ├── profiles/              # Founder & Investor profiles
│   ├── videos/                # Video management
│   ├── signals/               # Interest signals (like/pass/maybe)
│   ├── matches/               # Matching & messaging
│   ├── legal/                 # Legal consent tracking
│   └── reports/               # Content reporting & moderation
│
├── manage.py
├── requirements.txt
├── .env.example
├── setup.bat                   # Windows setup script
├── setup.sh                    # Unix/Mac setup script
└── SETUP_GUIDE.md             # Detailed setup instructions
```

## 🔧 Configuration

### Environment Variables (.env)

```env
# Django settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ikonetu

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5000

# Redis (for WebSocket)
REDIS_URL=redis://localhost:6379/0

# Session settings
SESSION_COOKIE_AGE=604800
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_SAMESITE=None
SESSION_COOKIE_HTTPONLY=True
```

## 📡 API Endpoints

All endpoints maintain compatibility with the existing frontend:

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user
- `GET /api/auth/me` - Get current user

### Profiles
- `GET /api/founder/profile` - Get founder profile
- `PUT /api/founder/profile` - Update founder profile
- `GET /api/founder/profile/:userId` - Get specific founder
- `GET /api/investor/profile` - Get investor profile
- `PUT /api/investor/profile` - Update investor profile
- `GET /api/investor/profile/:userId` - Get specific investor

### Videos
- `GET /api/videos/feed` - Get video feed
- `GET /api/videos/my` - Get user's videos
- `GET /api/videos/:id` - Get specific video
- `POST /api/videos` - Create new video
- `PUT /api/videos/:id` - Update video

### Signals
- `POST /api/signals` - Send interest signal
- `GET /api/signals/received` - Get received signals
- `GET /api/signals/sent` - Get sent signals

### Matches
- `GET /api/matches` - Get all matches
- `POST /api/matches/:id/accept` - Accept match
- `GET /api/matches/:id/messages` - Get match messages
- `POST /api/matches/:id/messages` - Send message

### Legal
- `GET /api/legal/consent` - Get user consent
- `POST /api/legal/consent` - Record consent

### Reports (Admin)
- `POST /api/reports` - Create report
- `GET /api/admin/reports` - List reports
- `PUT /api/admin/reports/:id` - Update report status
- `GET /api/admin/users` - List all users
- `GET /api/admin/videos` - List all videos
- `PUT /api/admin/videos/:id/status` - Update video status

### Dashboard
- `GET /api/dashboard/stats` - Get user statistics

## 🔐 Authentication

The backend uses **session-based authentication** (compatible with the existing frontend):

- Sessions stored in PostgreSQL
- HttpOnly, Secure cookies
- CORS-enabled for cross-origin requests
- Rate limiting on auth endpoints (5 requests/minute)

## 🧪 Testing

```bash
# Run tests
python manage.py test

# With coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 🚢 Deployment

### Using Gunicorn (Production)

```bash
# Install Gunicorn
pip install gunicorn

# Collect static files
python manage.py collectstatic --noinput

# Run with Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Using Daphne (WebSocket support)

```bash
# Run ASGI server for WebSocket
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 📝 Development Workflow

1. **Make changes to models**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Create superuser (admin access)**
   ```bash
   python manage.py createsuperuser
   ```

3. **Run development server**
   ```bash
   python manage.py runserver 8000
   ```

4. **Access admin panel**
   ```
   http://localhost:8000/admin
   ```

## 🔄 Migration from Node.js

### Key Changes

1. **Password Hashing**: 
   - Node.js: scrypt
   - Django: PBKDF2 (Django default)
   - **Action**: Users need to reset passwords OR implement custom auth backend

2. **Session Management**:
   - Node.js: express-session with connect-pg-simple
   - Django: Built-in session framework
   - **Action**: Sessions need to be recreated (users re-login)

3. **Database IDs**:
   - Both use UUIDs ✅
   - **Action**: No migration needed

4. **API Response Format**:
   - Maintained same structure ✅
   - **Action**: Frontend should work without changes

### Migration Steps

1. **Run both backends in parallel** (recommended)
   - Keep Node.js on port 5000
   - Run Django on port 8000
   - Gradually migrate users

2. **OR Direct cutover**
   - Export data from Node.js PostgreSQL
   - Import into Django (manual SQL scripts)
   - Update frontend API URL

## 🆘 Troubleshooting

### Database connection fails
```bash
# Check DATABASE_URL format
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
```

### CORS errors
```bash
# Update CORS_ALLOWED_ORIGINS in .env
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5000
```

### Session not persisting
```bash
# Check cookie settings in .env
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_SAMESITE=None
SESSION_COOKIE_HTTPONLY=True
```

### WebSocket not connecting
```bash
# Make sure Redis is running
redis-server

# Or with Docker
docker run -p 6379:6379 redis:alpine
```

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django Channels](https://channels.readthedocs.io/)
- [Setup Guide](SETUP_GUIDE.md) - Detailed setup instructions

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests
4. Submit pull request

## 📄 License

[Your License Here]

## 💬 Support

For issues or questions, please open an issue in the repository or contact the development team.

---

**Status**: ✅ Core structure complete | ⏳ Models implementation in progress

Built with ❤️ using Django REST Framework