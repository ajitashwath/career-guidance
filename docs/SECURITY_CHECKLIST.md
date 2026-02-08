# 🔒 SECURITY CHECKLIST
## Pre-Production Deployment Verification

**Use this checklist before deploying to production**

---

## ✅ Authentication & Authorization

- [ ] **JWT Secret Strength**  
  - [ ] JWT secret is at least 256 bits (32 characters)
  - [ ] Secret is stored in secure vault (not .env in production)
  - [ ] Secret rotation plan documented

- [ ] **Token Validation**  
  - [ ] Tokens expire appropriately (60 min default)
  - [ ] Refresh tokens have separate expiration (7 days)
  - [ ] Expired tokens are rejected
  - [ ] Invalid signatures are rejected
  - [ ] Audience claim is validated

- [ ] **Role-Based Access Control**  
  - [ ] Students cannot access recruiter endpoints
  - [ ] Students cannot access admin endpoints
  - [ ] Recruiters cannot access admin endpoints
  - [ ] Recruiters have read-only access (no modifications)
  - [ ] Admin actions are logged

---

## ✅ API Security

- [ ] **Rate Limiting**  
  - [ ] Rate limiting active on all endpoints
  - [ ] Redis backend configured and healthy
  - [ ] Different limits per endpoint category:
    - [ ] Auth: 5 req/min
    - [ ] LLM: 10 req/hour
    - [ ] Standard: 60 req/min
  - [ ] Rate limit headers returned to clients
  - [ ] 429 errors return retry-after

- [ ] **CORS Configuration**  
  - [ ] `allow_origins` is NOT `["*"]`
  - [ ] Only trusted origins whitelisted
  - [ ] Credentials enabled only for trusted origins
  - [ ] Methods restricted (no wildcard)

- [ ] **Input Validation**  
  - [ ] All text fields have max length
  - [ ] HTML/script tags stripped from inputs
  - [ ] SQL injection patterns blocked
  - [ ] UUID validation on path parameters
  - [ ] Email validation on email fields

- [ ] **Mass Assignment Protection**  
  - [ ] Computed fields marked as readonly in Pydantic
  - [ ] Admin-only fields cannot be set by users
  - [ ] Scores cannot be manipulated directly
  - [ ] Update endpoints use explicit field whitelists

---

## ✅ LLM Security

- [ ] **Prompt Injection Prevention**  
  - [ ] User input sanitized before LLM calls
  - [ ] Injection patterns detected and blocked
  - [ ] XML delimiters used to separate user input
  - [ ] System prompts isolated from user input

- [ ] **Output Filtering**  
  - [ ] PII filtered from LLM outputs (emails, phones)
  - [ ] Output length limited
  - [ ] Script tags removed from outputs
  - [ ] Context isolation validated per request

- [ ] **Rate Limiting**  
  - [ ] LLM endpoints have strict rate limits
  - [ ] Cost monitoring alerts configured
  - [ ] Per-user LLM quotas enforced

---

## ✅ Data Protection

- [ ] **Secrets Management**  
  - [ ] API keys in secure vault (Secret Manager, not .env)
  - [ ] Database credentials encrypted
  - [ ] JWT secret not in source control
  - [ ] .env not committed to git (.gitignore verified)

- [ ] **Database Security**  
  - [ ] RLS (Row Level Security) enabled
  - [ ] Service role key usage justified
  - [ ] Prepared statements used (SQL injection protection)
  - [ ] Connection limits configured

- [ ] **Audit Logging**  
  - [ ] All requests logged with user ID
  - [ ] Failed auth attempts logged
  - [ ] Admin actions specially logged
  - [ ] PII redacted from logs
  - [ ] Logs shipped to SIEM/monitoring tool

---

## ✅ Infrastructure & Deployment

- [ ] **Docker Security**  
  - [ ] Running as non-root user ✅ (already configured)
  - [ ] Base image is minimal (slim) ✅
  - [ ] Image scanned for vulnerabilities
  - [ ] Secrets not in Dockerfile
  - [ ] Health checks configured ✅

- [ ] **Network Security**  
  - [ ] HTTPS enforced in production
  - [ ] HSTS header enabled
  - [ ] Internal services not exposed publicly
  - [ ] Redis not externally accessible

- [ ] **Monitoring & Alerting**  
  - [ ] Error rates monitored
  - [ ] Failed auth attempts trigger alerts
  - [ ] High rate of 429s alert configured
  - [ ] Anomaly detection in place

---

## ✅ Error Handling

- [ ] **Production Error Messages**  
  - [ ] Stack traces NOT returned in prod (DEBUG=false)
  - [ ] Generic error messages for 500 errors
  - [ ] Request IDs in all error responses
  - [ ] Detailed errors only in logs

- [ ] **Security Headers**  
  - [ ] X-Content-Type-Options: nosniff
  - [ ] X-Frame-Options: DENY
  - [ ] X-XSS-Protection enabled
  - [ ] Content-Security-Policy configured
  - [ ] Strict-Transport-Security for HTTPS

---

## ✅ Testing & Compliance

- [ ] **Security Testing**  
  - [ ] All security tests passing (`pytest tests/security/`)
  - [ ] Manual penetration testing completed
  - [ ] OWASP ZAP scan passed
  - [ ] Dependency scan shows no critical CVEs

- [ ] **Dependency Management**  
  - [ ] `safety check` passing (no known vulnerabilities)
  - [ ] `bandit` SAST scan passing
  - [ ] Dependencies updated to latest secure versions
  - [ ] Dependabot/Snyk configured

- [ ] **Compliance**  
  - [ ] GDPR data export/deletion endpoints ready
  - [ ] Data retention policy documented
  - [ ] Consent management in place
  - [ ] Incident response playbook created
  - [ ] Breach notification plan documented

---

## ✅ Incident Response

- [ ] **Preparedness**  
  - [ ] Security contacts documented
  - [ ] Escalation path defined
  - [ ] Rollback procedure tested
  - [ ] Backup and recovery tested
  - [ ] Disaster recovery plan in place

---

## 📋 FINAL VERIFICATION

Before going live, run:

```bash
# 1. Security tests
pytest tests/security/ -v

# 2. Dependency scan
safety check
bandit -r app/ -ll

# 3. Verify environment
python -c "from app.core.config import get_settings; s = get_settings(); assert s.debug == False; assert '*' not in s.allowed_origins; print('✅ Config OK')"

# 4. Check Redis connection
redis-cli ping

# 5. Verify rate limiting works
curl -I http://localhost:8000/health
# Should see X-RateLimit headers

# 6. Test error messages don't leak info
# (with DEBUG=false, errors should be generic)
```

---

## 🚨 CRITICAL - DO NOT DEPLOY IF:

- ❌ DEBUG=true in production
- ❌ JWT secret is weak or default
- ❌ CORS allows all origins (`allow_origins=["*"]`)
- ❌ API keys in .env file (not vault)
- ❌ Rate limiting not active
- ❌ Security tests failing
- ❌ Critical CVEs in dependencies

---

**Checklist Completed By**: ________________  
**Date**: ________________  
**Reviewed By**: ________________  
**Approved for Production**: ☐ YES  ☐ NO

