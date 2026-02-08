#!/bin/bash

# Security Scan Script
# Runs all security checks for the Career Intelligence Platform

set -e

echo "🔒 Starting Security Scan..."
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. Check Python environment
echo ""
echo "1️⃣ Checking Python environment..."
python --version || { echo "Python not found!"; exit 1; }
print_status 0 "Python environment OK"

# 2. Install/update dependencies
echo ""
echo "2️⃣ Checking dependencies..."
pip install -q -r requirements.txt
print_status 0 "Dependencies installed"

# 3. Run safety check (dependency vulnerabilities)
echo ""
echo "3️⃣ Running dependency vulnerability scan..."
if safety check --json > safety_report.json 2>&1; then
    print_status 0 "No known vulnerabilities in dependencies"
else
    print_warning "Vulnerabilities found in dependencies - check safety_report.json"
    cat safety_report.json
fi

# 4. Run bandit (SAST for Python)
echo ""
echo "4️⃣ Running static security analysis (Bandit)..."
if bandit -r app/ -ll -f json -o bandit_report.json 2>&1; then
    print_status 0 "No high/critical security issues found"
else
    print_warning "Security issues found by Bandit - check bandit_report.json"
    bandit -r app/ -ll
fi

# 5. Run security tests
echo ""
echo "5️⃣ Running security tests..."
if pytest tests/security/ -v --tb=short; then
    print_status 0 "All security tests passed"
else
    print_warning "Some security tests failed"
fi

# 6. Check configuration security
echo ""
echo "6️⃣ Checking configuration security..."

# Check DEBUG mode
if grep -q "DEBUG=true" .env 2>/dev/null; then
    print_warning "DEBUG=true in .env - should be false in production!"
else
    print_status 0 "DEBUG mode configuration OK"
fi

# Check CORS configuration
python -c "
from app.core.config import get_settings
s = get_settings()
if '*' in s.allowed_origins:
    print('❌ CORS allows all origins - SECURITY RISK!')
    exit(1)
else:
    print('✅ CORS properly configured')
" || exit 1

# Check JWT secret strength
python -c "
from app.core.config import get_settings
s = get_settings()
if len(s.supabase_jwt_secret) < 32:
    print('⚠️  JWT secret is weak (< 32 characters)')
    exit(1)
else:
    print('✅ JWT secret strength OK')
"

# 7. Check for secrets in code
echo ""
echo "7️⃣ Checking for secrets in source code..."
if grep -r -i -E "(api_key|password|secret).*=.*['\"][^'\"]+['\"]" app/ --exclude-dir=__pycache__ 2>/dev/null; then
    print_warning "Potential hardcoded secrets found in source code!"
else
    print_status 0 "No hardcoded secrets found"
fi

# 8. Check Redis connection (for rate limiting)
echo ""
echo "8️⃣ Checking Redis connection..."
if redis-cli ping > /dev/null 2>&1; then
    print_status 0 "Redis connection OK"
else
    print_warning "Redis not accessible - rate limiting will use in-memory storage"
fi

# 9. Verify security headers
echo ""
echo "9️⃣ Verifying security headers (requires running server)..."
print_warning "Start server with 'uvicorn app.main:app' to test headers"

# 10. Generate report
echo ""
echo "🔟 Generating security report..."
cat > security_scan_report.txt << EOF
Security Scan Report
====================
Date: $(date)
Scan Type: Automated Security Check

Dependency Scan: See safety_report.json
SAST Scan: See bandit_report.json
Security Tests: $(pytest tests/security/ -q --tb=no 2>&1 || echo "FAILED")

Configuration Checks:
- DEBUG mode: $(grep "DEBUG=" .env 2>/dev/null || echo "Not set")
- CORS origins: $(python -c "from app.core.config import get_settings; print(get_settings().allowed_origins)" 2>/dev/null || echo "Error")
- Redis: $(redis-cli ping 2>/dev/null || echo "Not available")

Recommendations:
1. Review safety_report.json for dependency updates
2. Review bandit_report.json for code security issues
3. Ensure DEBUG=false in production
4. Verify CORS only allows trusted origins
5. Test rate limiting with load test

Next Steps:
- Fix any critical/high severity issues
- Update dependencies with known vulnerabilities
- Run penetration testing
- Review audit logs for anomalies
EOF

print_status 0 "Security report generated: security_scan_report.txt"

# Summary
echo ""
echo "=============================="
echo "✅ Security Scan Complete"
echo "=============================="
echo ""
echo "Reports generated:"
echo "  - security_scan_report.txt (summary)"
echo "  - safety_report.json (dependency vulnerabilities)"
echo "  - bandit_report.json (static analysis)"
echo ""
echo "Review all reports before deploying to production!"
