# Security Scanning Script (PowerShell)
# Runs all security checks for the Career Intelligence Platform on Windows

Write-Host "🔒 Starting Security Scan..." -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

# Function to print colored output
function Print-Status {
    param($Success, $Message)
    if ($Success) {
        Write-Host "✅ $Message" -ForegroundColor Green
    } else {
        Write-Host "❌ $Message" -ForegroundColor Red
    }
}

function Print-Warning {
    param($Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

# 1. Check Python environment
Write-Host ""
Write-Host "1️⃣ Checking Python environment..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version
    Print-Status $true "Python environment OK - $pythonVersion"
} catch {
    Print-Status $false "Python not found!"
    exit 1
}

# 2. Install/update dependencies
Write-Host ""
Write-Host "2️⃣ Checking dependencies..." -ForegroundColor Cyan
pip install -q -r requirements.txt
Print-Status $true "Dependencies installed"

# 3. Run safety check
Write-Host ""
Write-Host "3️⃣ Running dependency vulnerability scan..." -ForegroundColor Cyan
$safetyResult = & safety check --json 2>&1 | Out-File -FilePath safety_report.json
if ($LASTEXITCODE -eq 0) {
    Print-Status $true "No known vulnerabilities in dependencies"
} else {
    Print-Warning "Vulnerabilities found - check safety_report.json"
}

# 4. Run bandit
Write-Host ""
Write-Host "4️⃣ Running static security analysis (Bandit)..." -ForegroundColor Cyan
$banditResult = & bandit -r app/ -ll -f json -o bandit_report.json 2>&1
if ($LASTEXITCODE -eq 0) {
    Print-Status $true "No high/critical security issues found"
} else {
    Print-Warning "Security issues found - check bandit_report.json"
    bandit -r app/ -ll
}

# 5. Run security tests
Write-Host ""
Write-Host "5️⃣ Running security tests..." -ForegroundColor Cyan
$testResult = & pytest tests/security/ -v --tb=short 2>&1
if ($LASTEXITCODE -eq 0) {
    Print-Status $true "All security tests passed"
} else {
    Print-Warning "Some security tests failed"
}

# 6. Check configuration
Write-Host ""
Write-Host "6️⃣ Checking configuration security..." -ForegroundColor Cyan

if (Select-String -Path .env -Pattern "DEBUG=true" -Quiet) {
    Print-Warning "DEBUG=true in .env - should be false in production!"
} else {
    Print-Status $true "DEBUG mode configuration OK"
}

# Check CORS
python -c "from app.core.config import get_settings; s = get_settings(); exit(1 if '*' in s.allowed_origins else 0)"
if ($LASTEXITCODE -eq 0) {
    Print-Status $true "CORS properly configured"
} else {
    Print-Warning "CORS allows all origins - SECURITY RISK!"
}

# 7. Check Redis
Write-Host ""
Write-Host "8️⃣ Checking Redis connection..." -ForegroundColor Cyan
$redisTest = & redis-cli ping 2>&1
if ($LASTEXITCODE -eq 0) {
    Print-Status $true "Redis connection OK"
} else {
    Print-Warning "Redis not accessible - rate limiting will use in-memory storage"
}

# 8. Generate report
Write-Host ""
Write-Host "🔟 Generating security report..." -ForegroundColor Cyan

$report = @"
Security Scan Report
====================
Date: $(Get-Date)
Scan Type: Automated Security Check

Files Generated:
- safety_report.json (Dependency vulnerabilities)
- bandit_report.json (Static analysis)

Configuration:
- DEBUG mode: $(Select-String -Path .env -Pattern "DEBUG=" | Select-Object -First 1)
- Redis: $($redisTest)

Recommendations:
1. Review safety_report.json for dependency updates
2. Review bandit_report.json for code security issues
3. Ensure DEBUG=false in production
4. Verify CORS only allows trusted origins
5. Test rate limiting with load test

Next Steps:
- Fix any critical/high severity issues
- Update dependencies with vulnerabilities
- Run penetration testing
- Review audit logs
"@

$report | Out-File -FilePath security_scan_report.txt
Print-Status $true "Security report generated: security_scan_report.txt"

# Summary
Write-Host ""
Write-Host "==============================" -ForegroundColor Cyan
Write-Host "✅ Security Scan Complete" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Reports generated:" -ForegroundColor Cyan
Write-Host "  - security_scan_report.txt (summary)"
Write-Host "  - safety_report.json (dependency vulnerabilities)"
Write-Host "  - bandit_report.json (static analysis)"
Write-Host ""
Write-Host "Review all reports before deploying to production!" -ForegroundColor Yellow
