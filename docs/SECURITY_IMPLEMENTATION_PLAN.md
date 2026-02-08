# 🛡️ SECURITY IMPLEMENTATION PLAN
## Step-by-Step Hardening Guide

**Target System**: Career Intelligence API  
**Timeline**: 4 weeks  
**Priority**: CRITICAL → HIGH → MEDIUM

---

# WEEK 1: CRITICAL FIXES

## ✅ Task 1: Rate Limiting Implementation

### Files to Create/Modify:
1. `app/middleware/rate_limiting.py` (NEW)
2. `requirements.txt` (UPDATE - add slowapi, redis)
3. `app/main.py` (UPDATE - add middleware)
4. `docker-compose.yml` (UPDATE - add Redis service)

### Implementation Details:
- Use SlowAPI for rate limiting
- Redis backend for distributed rate limiting
- Different limits per endpoint category:
  - Auth: 5 req/min
  - LLM: 10 req/hour  
  - Standard: 60 req/min
  - Admin: 30 req/min

---

## ✅ Task 2: CORS Configuration Fix

### Files to Modify:
1. `app/main.py`
2. `app/core/config.py`

### Changes:
- Add `ALLOWED_ORIGINS` to environment config
- Replace `allow_origins=["*"]` with whitelist
- Enable credentials only for trusted origins

---

## ✅ Task 3: Secrets Management

### Files to Create/Modify:
1. `app/core/secrets.py` (NEW)
2. `app/core/config.py` (UPDATE)
3. `.env.example` (UPDATE with vault instructions)

### Implementation:
- Integrate Google Secret Manager or AWS Secrets Manager
- Remove secrets from `.env` in production
- Add secret rotation automation
- Use Docker secrets in compose file

---

## ✅ Task 4: Audit Logging Middleware

### Files to Create:
1. `app/middleware/audit_logging.py` (NEW)
2. `app/middleware/__init__.py` (NEW)

### Features:
- Log all API requests with:
  - User ID
  - IP address
  - Endpoint
  - Method
  - Status code
  - Timestamp
- Special logging for:
  - Failed auth attempts
  - Admin actions
  - Data modifications

---

## ✅ Task 5: Strict Field Validation (Mass Assignment Fix)

### Files to Modify:
1. `app/schemas/profiles.py`
2. `app/api/students.py`

### Changes:
- Add `Field(readonly=True)` to all computed/admin fields
- Create separate update schemas with explicit whitelists
- Reject unknown fields in requests

---

# WEEK 2: HIGH-PRIORITY FIXES

## ✅ Task 6: LLM Security Layer

### Files to Create/Modify:
1. `app/security/llm_security.py` (NEW)
2. `app/core/llm.py` (UPDATE)
3. `app/intelligence/ai_service.py` (UPDATE)

### Features:
- Input sanitization for prompts
- Prompt injection detection
- Output filtering for PII
- Context isolation per user
- Rate limiting on LLM calls

---

## ✅ Task 7: Secure Error Handling

### Files to Create/Modify:
1. `app/middleware/error_handler.py` (NEW)
2. `app/main.py` (UPDATE)

### Features:
- Global exception handler
- Production vs debug error modes
- Generic error messages in production
- Detailed logs (but not in responses)

---

## ✅ Task 8: Request/Response Logging

### Files to Modify:
1. `app/middleware/audit_logging.py` (ENHANCE)

### Features:
- Structured logging (JSON)
- PII redaction in logs
- Request ID correlation
- Performance metrics

---

## ✅ Task 9: Security Headers Middleware

### Files to Create:
1. `app/middleware/security_headers.py` (NEW)

### Headers to Add:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`
- `Content-Security-Policy: default-src 'self'`

---

# WEEK 3: MEDIUM-PRIORITY & TESTING

## ✅ Task 10: Input Validation Enhancement

### Files to Create/Modify:
1. `app/security/validators.py` (NEW)
2. All schema files (UPDATE)

### Features:
- Email validation
- UUID validation
- String sanitization (XSS prevention)
- Length limits on all text fields
- Regex patterns for structured data

---

## ✅ Task 11: Automated Security Testing

### Files to Create:
1. `tests/security/test_auth.py` (NEW)
2. `tests/security/test_authorization.py` (NEW)
3. `tests/security/test_injection.py` (NEW)
4. `tests/security/test_rate_limiting.py` (NEW)

### Test Coverage:
- Auth bypass attempts
- IDOR exploitation
- SQL injection vectors
- Prompt injection
- Rate limit enforcement

---

## ✅ Task 12: Dependency Scanning

### Files to Create:
1. `.github/workflows/security-scan.yml` (NEW)
2. `scripts/security-scan.sh` (NEW)

### Tools to Integrate:
- `safety check` (Python vulnerabilities)
- `bandit` (SAST for Python)
- `trivy` (container scanning)

---

# WEEK 4: ONGOING HARDENING

## ✅ Task 13: Database Security

### Files to Create/Modify:
1. `docs/DATABASE_SECURITY.md` (NEW)
2. `app/db/supabase.py` (ENHANCE)

### Enhancements:
- Verify RLS policies are enabled
- Add prepared statement verification
- Implement query logging
- Add connection pooling limits

---

## ✅ Task 14: Incident Response Playbook

### Files to Create:
1. `docs/INCIDENT_RESPONSE.md` (NEW)
2. `scripts/incident-response.sh` (NEW)

### Contents:
- Detection procedures
- Escalation paths
- Containment steps
- Evidence collection
- Post-mortem template

---

## ✅ Task 15: Compliance Documentation

### Files to Create:
1. `docs/GDPR_COMPLIANCE.md` (NEW)
2. `docs/DATA_RETENTION.md` (NEW)
3. `app/api/gdpr.py` (NEW - data export/deletion endpoints)

---

# FILE MANIFEST

## New Files to Create:

```
app/
├── middleware/
│   ├── __init__.py
│   ├── rate_limiting.py
│   ├── audit_logging.py
│   ├── error_handler.py
│   └── security_headers.py
├── security/
│   ├── __init__.py
│   ├── llm_security.py
│   ├── validators.py
│   └── secrets.py (if not using vault)
└── api/
    └── gdpr.py

tests/
└── security/
    ├── __init__.py
    ├── test_auth.py
    ├── test_authorization.py
    ├── test_injection.py
    └── test_rate_limiting.py

docs/
├── DATABASE_SECURITY.md
├── INCIDENT_RESPONSE.md
├── GDPR_COMPLIANCE.md
└── DATA_RETENTION.md

scripts/
├── security-scan.sh
└── incident-response.sh

.github/
└── workflows/
    └── security-scan.yml
```

## Files to Modify:

```
app/
├── main.py (add middleware, error handlers)
├── core/
│   ├── config.py (add security settings)
│   ├── auth.py (enhance JWT validation)
│   └── llm.py (add security layer)
├── api/
│   ├── admin.py (add audit logs)
│   ├── students.py (field validation)
│   └── ai.py (LLM security)
└── db/
    └── supabase.py (enhanced error handling)

requirements.txt (add security dependencies)
docker-compose.yml (add Redis, secrets)
Dockerfile (security hardening)
.env.example (update with vault info)
```

---

# DEPENDENCY ADDITIONS

Add to `requirements.txt`:

```txt
# Rate Limiting
slowapi==0.1.9
redis==5.0.1

# Security
pydantic[email]==2.6.1
python-multipart==0.0.9
bleach==6.1.0  # XSS prevention

# Secrets Management (choose one)
google-cloud-secret-manager==2.18.2  # For GCP
boto3==1.34.34  # For AWS Secrets Manager

# Security Scanning
safety==3.0.1
bandit==1.7.6

# Monitoring
python-json-logger==2.0.7
sentry-sdk[fastapi]==1.40.0  # Error tracking
```

---

# TESTING CHECKLIST

Before deploying to production, verify:

- [ ] Rate limiting active on all endpoints
- [ ] CORS restricted to known origins
- [ ] Secrets loaded from vault (not .env)
- [ ] Audit logs writing to persistent storage
- [ ] Field validation rejecting unknown fields
- [ ] LLM security layer blocking injection attempts
- [ ] Error messages sanitized in production
- [ ] Security headers present in all responses
- [ ] All security tests passing
- [ ] Dependency scan shows no critical CVEs
- [ ] Manual penetration test completed
- [ ] Incident response playbook reviewed
- [ ] GDPR endpoints functional
- [ ] Backup and recovery tested

---

# DEPLOYMENT SEQUENCE

1. **Staging Deployment**:
   ```bash
   # Deploy to staging with all security features
   docker-compose -f docker-compose.staging.yml up -d
   
   # Run security tests
   pytest tests/security/ -v
   
   # Manual penetration testing
   # Run OWASP ZAP scan
   ```

2. **Production Deployment**:
   ```bash
   # Enable maintenance mode
   # Deploy with zero-downtime (blue-green)
   # Verify security headers
   # Monitor for 24h
   # Full rollback plan ready
   ```

3. **Post-Deployment**:
   ```bash
   # Verify rate limiting
   # Check audit logs
   # Monitor error rates
   # Review SIEM alerts
   ```

---

**Implementation Start**: Immediately  
**Target Completion**: 4 weeks from start  
**Security Re-Assessment**: Post-implementation

