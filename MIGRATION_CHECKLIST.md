# Ikonetu Backend Migration Checklist

## Phase 1: Initial Setup ✅ COMPLETE

- [x] Create Django project structure
- [x] Set up virtual environment
- [x] Configure settings.py
- [x] Create requirements.txt
- [x] Set up CORS and sessions
- [x] Create custom User model
- [x] Implement authentication endpoints
- [x] Add rate limiting
- [x] Configure WebSocket support (Channels)
- [x] Create all app directories

## Phase 2: Model Implementation ⏳ IN PROGRESS

### accounts app ✅ DONE
- [x] User model with roles
- [x] Custom authentication
- [x] Session management
- [x] Rate limiting middleware

### profiles app ⏳ TODO
- [ ] FounderProfile model
- [ ] InvestorProfile model
- [ ] Profile serializers
- [ ] Profile views and URLs
- [ ] Profile update validation

### videos app ⏳ TODO
- [ ] Video model
- [ ] Video status enum
- [ ] Video serializers
- [ ] Feed algorithm implementation
- [ ] View count tracking
- [ ] Video filtering for investors

### signals app ⏳ TODO
- [ ] Signal model (interested/maybe/pass)
- [ ] Signal serializers
- [ ] Signal creation logic
- [ ] Signal validation (no self-signaling)
- [ ] Received/sent signal views

### matches app ⏳ TODO
- [ ] Match model
- [ ] Message model
- [ ] Match acceptance logic
- [ ] Message serializers
- [ ] WebSocket consumer for real-time messages
- [ ] Unread message tracking

### legal app ⏳ TODO
- [ ] LegalConsent model
- [ ] Consent serializers
- [ ] Consent views
- [ ] IP address tracking

### reports app ⏳ TODO
- [ ] Report model
- [ ] Report status enum
- [ ] Report serializers
- [ ] Admin report views
- [ ] Report resolution tracking

## Phase 3: Frontend Integration

### Update Frontend Configuration
- [ ] Update API base URL in queryClient.ts
- [ ] Or add proxy configuration in vite.config.ts
- [ ] Update WebSocket connection URL
- [ ] Test CORS configuration

### Test Each Endpoint
#### Authentication
- [ ] POST /api/auth/register
- [ ] POST /api/auth/login
- [ ] POST /api/auth/logout
- [ ] GET /api/auth/me

#### Profiles
- [ ] GET /api/founder/profile
- [ ] PUT /api/founder/profile
- [ ] GET /api/founder/profile/:userId
- [ ] GET /api/investor/profile
- [ ] PUT /api/investor/profile
- [ ] GET /api/investor/profile/:userId

#### Videos
- [ ] GET /api/videos/feed
- [ ] GET /api/videos/my
- [ ] GET /api/videos/:id
- [ ] POST /api/videos
- [ ] PUT /api/videos/:id

#### Signals
- [ ] POST /api/signals
- [ ] GET /api/signals/received
- [ ] GET /api/signals/sent

#### Matches
- [ ] GET /api/matches
- [ ] POST /api/matches/:id/accept
- [ ] GET /api/matches/:id/messages
- [ ] POST /api/matches/:id/messages
- [ ] WebSocket real-time messaging

#### Legal
- [ ] GET /api/legal/consent
- [ ] POST /api/legal/consent

#### Reports & Admin
- [ ] POST /api/reports
- [ ] GET /api/admin/reports (admin only)
- [ ] PUT /api/admin/reports/:id (admin only)
- [ ] GET /api/admin/users (admin only)
- [ ] GET /api/admin/videos (admin only)
- [ ] PUT /api/admin/videos/:id/status (admin only)

#### Dashboard
- [ ] GET /api/dashboard/stats (role-specific)

## Phase 4: Database Migration (if needed)

### Option A: Fresh Start
- [ ] Run migrations on empty database
- [ ] Create test users
- [ ] Test all functionality

### Option B: Migrate Existing Data
- [ ] Export users from Node.js database
- [ ] Convert password hashes (scrypt → PBKDF2)
- [ ] Export profiles
- [ ] Export videos
- [ ] Export signals
- [ ] Export matches
- [ ] Export messages
- [ ] Export legal consents
- [ ] Export reports
- [ ] Import all data into Django
- [ ] Verify data integrity

## Phase 5: Testing

### Unit Tests
- [ ] Test User model
- [ ] Test authentication
- [ ] Test profiles
- [ ] Test videos
- [ ] Test signals
- [ ] Test matches
- [ ] Test messages
- [ ] Test legal consent
- [ ] Test reports

### Integration Tests
- [ ] Test complete user registration flow
- [ ] Test founder profile creation
- [ ] Test investor profile creation
- [ ] Test video upload and approval
- [ ] Test signaling flow
- [ ] Test matching flow
- [ ] Test messaging flow
- [ ] Test reporting flow
- [ ] Test admin moderation

### Frontend Integration Tests
- [ ] Login flow
- [ ] Registration flow
- [ ] Profile updates
- [ ] Video feed
- [ ] Signaling
- [ ] Matching
- [ ] Real-time messaging
- [ ] Legal consent

## Phase 6: Production Deployment

### Pre-deployment
- [ ] Set DEBUG=False
- [ ] Configure production DATABASE_URL
- [ ] Set strong SECRET_KEY
- [ ] Configure ALLOWED_HOSTS
- [ ] Set up SSL certificates
- [ ] Configure production CORS_ALLOWED_ORIGINS
- [ ] Set up Redis for production
- [ ] Configure static file serving
- [ ] Set up media file storage

### Deployment
- [ ] Deploy Django backend
- [ ] Deploy Daphne for WebSocket
- [ ] Configure Nginx/Apache reverse proxy
- [ ] Set up SSL/TLS
- [ ] Configure firewall
- [ ] Set up monitoring
- [ ] Set up logging
- [ ] Configure backups

### Post-deployment
- [ ] Test all endpoints in production
- [ ] Monitor error logs
- [ ] Monitor performance
- [ ] Test WebSocket connections
- [ ] Verify CORS working
- [ ] Verify sessions persisting
- [ ] Load testing

## Current Status Summary

### ✅ Completed
1. Django project structure created
2. Custom User model with role-based access
3. Authentication system (register, login, logout, me)
4. Session-based auth with CORS support
5. Rate limiting on auth endpoints
6. Custom exception handling
7. WebSocket infrastructure (Channels)
8. All app directories and base files created

### ⏳ In Progress / Next Steps
1. **PRIORITY 1**: Implement all models (profiles, videos, signals, matches, legal, reports)
2. **PRIORITY 2**: Create serializers for all models
3. **PRIORITY 3**: Implement views and URL routing
4. **PRIORITY 4**: Add WebSocket consumer for real-time messaging
5. **PRIORITY 5**: Frontend integration and testing

## Quick Start Commands

```bash
# Setup (first time only)
./setup.sh  # or setup.bat on Windows

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver 8000

# Run with WebSocket support
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Make migrations after model changes
python manage.py makemigrations
python manage.py migrate

# Create app (if needed)
python manage.py startapp appname

# Run tests
python manage.py test

# Collect static files
python manage.py collectstatic
```

## Development Workflow

1. **Start both servers** (during migration):
   ```bash
   # Terminal 1: Django backend
   cd ikonetu-backend
   python manage.py runserver 8000
   
   # Terminal 2: Frontend
   cd ikonetu
   npm run dev
   
   # Terminal 3: Redis (for WebSocket)
   redis-server
   ```

2. **Update frontend to use new backend**:
   - Option A: Update fetch URLs to `http://localhost:8000`
   - Option B: Add proxy in vite.config.ts

3. **Test incrementally**:
   - Test each endpoint as you implement it
   - Use Postman/Thunder Client for API testing
   - Use browser dev tools to debug CORS issues

## Notes

- **Password Migration**: Users will need to reset passwords when migrating from Node.js (different hash algorithms)
- **Session Migration**: Sessions won't transfer; users need to re-login
- **Database IDs**: Both use UUIDs, so ID compatibility is maintained
- **API Compatibility**: Response formats match the original Node.js API

## Support

If you encounter issues:
1. Check the SETUP_GUIDE.md for detailed instructions
2. Review Django documentation
3. Check CORS and session cookie settings
4. Verify database connection string
5. Ensure Redis is running for WebSocket

---

**Last Updated**: December 13, 2025
**Status**: Foundation Complete, Models In Progress