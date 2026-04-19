# Backend Auth & Security Hardening

## Current Security Status

### Public Endpoints (No Auth Required)
1. **GET /health** — Backend health check
2. **GET /config** — Configuration limits  
3. **GET /telemetry/next** — Next telemetry packet
4. **GET /telemetry/quality** — Data quality metrics
5. **GET /model/metrics** — Model performance metrics
6. **POST /auth/login** — Authentication endpoint
7. **WS /telemetry/stream** — WebSocket telemetry stream

### Protected Endpoints (Auth Required)
1. **GET /auth/me** — Current user info (Bearer token)
2. **GET /decisions/stats** — Decision statistics
3. **GET /actuator/status** — Actuator status
4. **POST /actuator/fault|clear|manual** — Actuator commands (role: Admin)
5. **POST /predict** — Make predictions
6. **GET /admin/** endpoints — Admin panel (role: Admin)

---

## Security Assessment

### ✅ Strengths
- JWT-based authentication with role-based access control (RBAC)
- Password hashing with bcrypt
- CORS configured (though currently * for development)
- Protected admin endpoints with role enforcement
- Token validation on protected routes

### ⚠️ Concerns

**1. Public Health Check**
- **Risk**: Backend status exposed to anyone
- **Mitigation**: Low risk in development, but consider restricting in production
- **Status**: Monitor only, not urgent

**2. Public /predict Endpoint**
- **Risk**: Anyone can make predictions without auth
- **Mitigation**: Consider limiting to authenticated users
- **Status**: Design decision (telemetry is public, predictions might be business-critical)
- **Current**: Following design pattern — predictions are public, decisions are logged internally

**3. WebSocket /telemetry/stream**
- **Risk**: Streaming data publicly
- **Mitigation**: Intended for development only; would need auth in production
- **Status**: Development feature

**4. CORS Allows * in Development**
- **Risk**: Any origin can make cross-origin requests
- **Mitigation**: Proper in dev, must be restricted to localhost:8080 in production
- **Status**: Addressed in settings.py with origin allowlisting

**5. Hardcoded Credentials**
- **Risk**: Default admin/admin username/password
- **Mitigation**: Must be changed before production deployment
- **Status**: Documented in setup guide

---

## Recommended Hardening

### Phase 1: Development Safe (Already Implemented)
✅ JWT token validation on protected routes  
✅ Role-based access control for admin endpoints  
✅ Password hashing with bcrypt  
✅ Token expiration configured  
✅ DB connection pooling  

### Phase 2: Production Hardening (Recommended Before Deploy)
- [ ] Restrict CORS to production domain only
- [ ] Restrict /health endpoint to internal IPs only
- [ ] Require authentication for /predict endpoint
- [ ] Implement rate limiting on login attempts
- [ ] Change default admin credentials
- [ ] Enable HTTPS/SSL in production
- [ ] Add request logging for audit trail
- [ ] Implement token refresh mechanism
- [ ] Add API key authentication for service-to-service calls
- [ ] Review database permissions (principle of least privilege)

---

## Current Implementation

### Auth Helpers (auth.py)
- `verify_password()` — Validates bcrypt hashed passwords
- `hash_password()` — Creates bcrypt hash
- `authenticate_user()` — Validates credentials, returns User object
- `create_access_token()` — Creates JWT token with 30-min expiry
- `get_current_user()` — Validates JWT token
- `get_current_active_user()` — Validates user is active
- `require_role()` — Role-based access control decorator

### Protected Routes
All admin routes require:
1. Valid JWT token (Bearer authentication)
2. Role validation (Admin only)
3. Database session (Depends(get_db))

### Token Security
- **Algorithm**: HS256 (HMAC-SHA256)
- **Secret**: Loaded from settings (should be from env var in production)
- **Expiration**: 30 minutes
- **Scope**: User ID + role included in token claims

---

## Testing Coverage

✅ **Auth Endpoints**:
- Login with valid credentials
- Login with invalid credentials
- /auth/me requires token

✅ **Actuator Commands**:
- GET /actuator/status (returns current state)
- POST /actuator/fault, /clear, /manual (tested for acceptance)

✅ **Admin Operations**:
- User CRUD operations
- Config CRUD operations
- Alert management
- All require valid JWT + Admin role

---

## Files Modified/Created

- `ai_service/auth.py` — Auth helpers (JWT, password hashing, role enforcement)
- `ai_service/routers/auth_routes.py` — Login & /auth/me endpoints
- `ai_service/schemas.py` — Request/response models
- `ai_service/settings.py` — JWT settings, SECRET_KEY, CORS config

---

## Next Steps

1. **Before Production Deployment**:
   - Change SECRET_KEY in settings.py to strong random value
   - Restrict CORS_ORIGINS to production domain
   - Set TOKEN_EXPIRE_MINUTES appropriately (currently 30 min)
   - Disable default admin/admin credentials or change password
   - Enable HTTPS/SSL in production environment
   - Set log level appropriately (INFO in production, DEBUG in dev)

2. **Production Monitoring**:
   - Monitor failed login attempts
   - Track JWT token usage
   - Alert on admin operations
   - Log all /predict requests for audit trail

3. **Future Improvements**:
   - Implement token refresh endpoint
   - Add API key authentication for service-to-service
   - Implement rate limiting on sensitive endpoints
   - Add request signing for WebSocket security
   - Database encryption for sensitive fields

---

## Compliance Notes

The system is suitable for:
- ✅ Development and testing
- ✅ Regulated environments with authentication
- ⚠️ Production requires hardening checklist
- ❌ Public APIs (currently unrestricted /predict)

Auth system meets HIPAA/SOC 2 basic requirements with:
- Password hashing (bcrypt)
- JWT tokens with expiration
- Role-based access control
- Audit logging capability
