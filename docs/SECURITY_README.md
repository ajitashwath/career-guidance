# 🔐 Security Documentation & Quick Start

## Overview

This directory contains comprehensive security documentation and tools for the Career Intelligence Platform. After a thorough security assessment and hardening process, the system's security score improved from **3/10 to 8.5/10**.

---

## 📚 Documentation

### Core Documents

1. **[SECURITY_ASSESSMENT.md](./SECURITY_ASSESSMENT.md)**
   - Complete threat modeling (STRIDE methodology)
   - Vulnerability analysis with severity ratings
   - Red team attack simulations
   - Current security score: 8.5/10

2. **[SECURITY_IMPLEMENTATION_PLAN.md](./SECURITY_IMPLEMENTATION_PLAN.md)**
   - 4-week implementation roadmap
   - File manifest of all security components
   - Task breakdown by priority
   - Testing procedures

3. **[SECURITY_HARDENING_SUMMARY.md](./SECURITY_HARDENING_SUMMARY.md)**
   - Summary of all implemented features
   - Before/after metrics
   - Deployment guide
   - Compliance status

4. **[SECURITY_CHECKLIST.md](./SECURITY_CHECKLIST.md)**
   - Pre-production deployment verification
   - Sign-off checklist
   - Critical "do not deploy if" conditions

---

## ⚡ Quick Start

### Run Security Scan

**Windows (PowerShell)**:
```powershell
.\scripts\security-scan.ps1
```

**Linux/Mac (Bash)**:
```bash
chmod +x scripts/security-scan.sh
./scripts/security-scan.sh
```

This will:
- Check dependencies for vulnerabilities (safety)
- Run static analysis (bandit)
- Execute security tests (pytest)
- Verify configuration
- Generate security report

---

## 🛡️ Security Features Implemented

### ✅ Critical Fixes

1. **Rate Limiting** - Prevents API abuse, DoS, and LLM cost explosion
   - Redis-backed distributed rate limiting
   - Per-endpoint limits (auth: 5/min, LLM: 10/hour, standard: 60/min)
   - Returns 429 with Retry-After header

2. **CORS Fix** - Explicit origin whitelist (no more `allow_origins=["*"]`)
   - Configured via environment variable
   - Only trusted domains allowed

3. **LLM Security** - Multi-layer protection against prompt injection
   - Input sanitization and injection detection
   - Output PII filtering
   - Context isolation validation

4. **Audit Logging** - Comprehensive request/security event logging
   - All API requests logged with user ID, IP, duration
   - Failed auth attempts flagged
   - Admin actions specially logged
   - PII auto-redacted

5. **Error Handling** - No stack trace leaks in production
   - Generic errors in production (DEBUG=false)
   - Detailed errors only in logs
   - Request IDs for correlation

6. **Security Headers** - Protection against common web vulnerabilities
   - X-Content-Type-Options, X-Frame-Options, CSP, HSTS, etc.

---

## 🧪 Testing

### Run Security Tests

```bash
# All security tests
pytest tests/security/ -v

# Specific test categories
pytest tests/security/test_auth.py -v          # Authentication
pytest tests/security/test_authorization.py -v  # Authorization/RBAC
pytest tests/security/test_injection.py -v      # LLM security

# With coverage
pytest tests/security/ --cov=app --cov-report=html
```

### Manual Testing

```bash
# Test rate limiting
for i in {1..70}; do curl http://localhost:8000/health; done
# Should see 429 after limit

# Check security headers
curl -I http://localhost:8000/health | grep -E "X-|Strict|Content-Security"

# Verify CORS (should reject if origin not whitelisted)
curl -H "Origin: https://evil.com" http://localhost:8000/health
```

---

## 📋 Pre-Production Checklist

Before deploying, verify:

- [ ] DEBUG=false in production
- [ ] CORS restricted to known origins (no `*`)
- [ ] JWT secret is strong (≥32 chars)
- [ ] API keys in secure vault (not .env)
- [ ] Rate limiting active (test with curl)
- [ ] Security tests passing (`pytest tests/security/`)
- [ ] Dependency scan clean (`safety check`)
- [ ] SAST scan clean (`bandit -r app/`)
- [ ] Redis healthy (rate limiting backend)
- [ ] Audit logs shipping to monitoring tool

---

## 🚨 Critical Security Rules

### DO NOT Deploy If:

- ❌ `DEBUG=true` in production
- ❌ `allow_origins=["*"]` in CORS config
- ❌ JWT secret is weak or default
- ❌ API keys stored in .env file (should be in vault)
- ❌ Rate limiting not working
- ❌ Security tests failing
- ❌ Critical CVEs in dependencies

---

## 🔧 Configuration

### Environment Variables (Security)

```env
# CORS - whitelist only trusted origins
ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com

# Rate limiting - Redis backend
REDIS_URL=redis://redis:6379

# JWT settings
JWT_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Server
DEBUG=false  # MUST be false in production
```

---

## 📊 Security Metrics

| Category | Before | After |
|----------|--------|-------|
| **Overall Score** | 3/10 🔴 | 8.5/10 ✅ |
| **Rate Limiting** | ❌ None | ✅ All endpoints |
| **CORS** | ❌ Open | ✅ Whitelisted |
| **Audit Logs** | ❌ None | ✅ Comprehensive |
| **Error Leaks** | ❌ Stack traces | ✅ Generic messages |
| **LLM Security** | ❌ Vulnerable | ✅ Protected |

---

## 🔍 Security Scanning Tools

### Dependency Scanning
```bash
# Check for known vulnerabilities
safety check

# Auto-update vulnerable packages (review first!)
safety check --policy-file policy.yml
```

### Static Analysis (SAST)
```bash
# Python security linter
bandit -r app/ -ll  # Only high/critical

# Custom rules
bandit -r app/ -c bandit.yaml
```

### Dynamic Analysis (DAST)
```bash
# OWASP ZAP (requires ZAP installed)
zap-cli quick-scan http://localhost:8000

# Or use ZAP GUI for manual testing
```

---

## 🚀 Incident Response

If a security incident occurs:

1. **Identify & Contain**
   - Check audit logs: `grep "failed_auth" audit.log`
   - Block malicious IPs at firewall level
   - Revoke compromised tokens

2. **Investigate**
   - Review audit logs for attack pattern
   - Check for data exfiltration
   - Identify affected users

3. **Remediate**
   - Patch vulnerability
   - Rotate secrets if compromised
   - Force password resets if needed

4. **Document**
   - Create post-mortem
   - Update runbooks
   - Enhance detection rules

**Security Contacts**:
- Security Lead: [Your Team]
- On-Call: Check PagerDuty
- Bug Bounty: security@example.com

---

## 📱 Monitoring & Alerts

### Critical Alerts

Configure alerts for:
- **High auth failure rate** (>10 failures/min from one IP)
- **Rate limit breaches** (>100 429s/min)
- **Admin action anomalies** (admin actions outside business hours)
- **Error rate spike** (>100 500s/min)
- **PII detected in logs** (should never happen with our redaction)

### Dashboards

Monitor:
- Rate limit hits by endpoint
- Auth success/failure rates
- Response time P95/P99
- Error rates by status code
- LLM API costs (cost anomaly detection)

---

## 🎓 Security Best Practices

### For Developers

1. **Never commit secrets** - Use .gitignore, pre-commit hooks
2. **Validate all inputs** - Don't trust user data
3. **Use prepared statements** - Prevent SQL injection
4. **Sanitize outputs** - Prevent XSS
5. **Least privilege** - Give minimum necessary permissions
6. **Fail securely** - Default to deny, not allow
7. **Defense in depth** - Multiple layers of security

### For Operations

1. **Keep dependencies updated** - Automated scanning
2. **Monitor audit logs** - SIEM integration
3. **Regular pen testing** - Quarterly at minimum
4. **Incident response drills** - Practice makes perfect
5. **Secrets rotation** - Quarterly JWT secret rotation
6. **Backup verification** - Test restores regularly

---

## 📖 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [STRIDE Threat Modeling](https://docs.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CWE Top 25](https://cwe.mitre.org/top25/)

---

## 🤝 Contributing

Found a security issue? 

- **Critical/High**: Email security@example.com immediately
- **Medium/Low**: Create a private GitHub security advisory
- **Bug Bounty**: Submit via HackerOne (when program launches)

**DO NOT** create public GitHub issues for security vulnerabilities.

---

**Last Updated**: 2026-02-08  
**Security Version**: 2.0  
**Next Review**: 2026-05-08

