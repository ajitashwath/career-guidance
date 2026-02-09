# 🎯 Quick Start - Testing Your Career Intelligence Backend

## Current Status ✅

I've successfully configured your backend to use **OpenRouter** for AI and created a comprehensive testing suite!

---

## 🚦 What You Need to Do Now

### Step 1: Get Your API Keys & Credentials

You need to collect these credentials:

#### 1️⃣ Supabase Credentials (Required)
Go to your Supabase project dashboard:
- **SUPABASE_URL**: Your project URL (e.g., `https://xxxxx.supabase.co`)
- **SUPABASE_KEY**: Service role key (Settings → API → service_role key)
- **SUPABASE_JWT_SECRET**: JWT Secret (Settings → API → JWT Secret)

#### 2️⃣ OpenRouter API Key (Required for AI)
1. Visit https://openrouter.ai/
2. Sign up or log in
3. Go to "Keys" section
4. Create a new API key
5. Copy the key

#### 3️⃣ Test User Tokens (Optional but Recommended)
You'll need JWT tokens for testing. See the section "How to Get Test Tokens" below.

---

### Step 2: Configure .env File

A `.env` file has been created for you. Open it and fill in your credentials:

```bash
# Edit the .env file
notepad .env
```

**Update these values:**

```bash
# ===== REQUIRED - Supabase Configuration =====
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key-here
SUPABASE_JWT_SECRET=your-jwt-secret-here

# ===== REQUIRED - OpenRouter for AI =====
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# ===== OPTIONAL - Test Tokens =====
TEST_STUDENT_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
TEST_RECRUITER_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
TEST_ADMIN_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

### Step 3: Verify Configuration

Run this command to check if everything is configured correctly:

```bash
python check_config.py
```

You should see all ✓ green checkmarks for required items.

---

### Step 4: Install Dependencies (if needed)

```bash
pip install -r requirements.txt
```

---

### Step 5: Start the Server

```bash
uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

The server is now running! 🚀
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

---

### Step 6: Run Tests

**Open a NEW terminal** (keep the server running in the first one), then:

```bash
python test_all_endpoints.py
```

This will test all ~45 endpoints including all AI features powered by OpenRouter!

---

## 📊 Understanding Test Results

### Console Output

You'll see color-coded results:
- ✅ **Green checkmark** = Test passed
- ❌ **Red X** = Test failed
- ⊘ **Yellow** = Test skipped (missing auth token)

### Example Output:
```
================================================================================
                        AI Endpoints (OpenRouter)
================================================================================

Testing AI Profile Analysis...
✓ GET /ai/profile-analysis: Analysis completed

Testing AI Career Advice...
✓ POST /ai/career-advice: Advice generated

Testing AI Interview Preparation...
✓ POST /ai/interview-prep: Interview questions generated

Testing AI Skill Gap Analysis...
✓ POST /ai/skill-gaps: Skill gap analysis completed

Testing AI Resume Suggestions...
✓ GET /ai/resume-suggestions: Resume suggestions generated
```

### Detailed Report

After testing, check `test_report.json`:
```json
{
  "passed": 42,
  "failed": 0,
  "skipped": 3,
  "tests": [...]
}
```

This contains full request/response data for debugging.

---

## 🔑 How to Get Test Tokens

Test tokens are **optional** but allow comprehensive testing of all endpoints.

### Method 1: Using Supabase Dashboard

1. Go to Supabase Dashboard → Authentication → Users
2. Create test users with different roles
3. Get their JWT tokens from the user details

### Method 2: Using API Calls

```bash
# Sign up a student user
curl -X POST 'https://YOUR-PROJECT.supabase.co/auth/v1/signup' \
  -H "apikey: YOUR-ANON-KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@test.com",
    "password": "SecurePassword123!",
    "data": {
      "role": "student",
      "full_name": "Test Student"
    }
  }'

# Login to get JWT token
curl -X POST 'https://YOUR-PROJECT.supabase.co/auth/v1/token?grant_type=password' \
  -H "apikey: YOUR-ANON-KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@test.com",
    "password": "SecurePassword123!"
  }'
```

The response includes an `access_token` - use this as your `TEST_STUDENT_TOKEN`.

Repeat for recruiter and admin roles.

---

## 🎯 What Gets Tested

### All Endpoints Covered:

| Category | Count | Description |
|----------|-------|-------------|
| **System** | 2 | Health check, root endpoint |
| **Student Profile** | 14 | Profile, skills, education, experience, projects, certs |
| **Events** | 2 | Event types, emit events |
| **AI (OpenRouter)** | 5 | Profile analysis, career advice, interview prep, skill gaps, resume tips |
| **Recruiters** | 4+ | Candidate search, profiles, summaries, timelines |
| **Admin** | 5+ | Scoring debug, system stats, recomputation |

### AI Endpoints in Detail:

1. **GET /ai/profile-analysis**
   - Analyzes user's complete profile
   - Returns strengths, weaknesses, action items
   - Profile completeness score

2. **POST /ai/career-advice**
   - Personalized career guidance
   - Context-aware based on profile
   - Actionable next steps

3. **POST /ai/interview-prep**
   - Role-specific interview questions
   - Technical, behavioral, and role-specific
   - Preparation tips included

4. **POST /ai/skill-gaps**
   - Compares skills to target role
   - Identifies missing critical skills
   - Learning path recommendations

5. **GET /ai/resume-suggestions**
   - AI-powered resume improvements
   - ATS optimization tips
   - Specific actionable changes

---

## 🐛 Troubleshooting

### Issue: "Configuration incomplete"
**Solution:** Run `python check_config.py` to see what's missing

### Issue: "Connection refused" when running tests
**Solution:** Make sure the server is running in another terminal

### Issue: 500 errors on AI endpoints
**Solutions:**
1. Verify `OPENROUTER_API_KEY` is correct in `.env`
2. Check you have credits on OpenRouter (https://openrouter.ai/)
3. Ensure `LLM_PROVIDER=openrouter` in `.env`

### Issue: 401 Unauthorized errors
**Solutions:**
1. Test tokens may have expired - generate fresh ones
2. Ensure tokens are in correct format (just the token, no "Bearer" prefix)

### Issue: Many tests are skipped
**This is normal!** Tests requiring authentication are skipped if you haven't configured test tokens. The API still works - you just can't test authenticated endpoints automatically.

---

## 📚 Additional Resources

### Documentation Files Created:
- **API_TESTING_SUMMARY.md** - Complete overview of changes
- **TESTING_README.md** - User-friendly testing guide  
- **TESTING_GUIDE.md** - Detailed testing instructions
- **THIS FILE** - Quick start guide

### Helper Scripts:
- **check_config.py** - Verify your configuration
- **test_all_endpoints.py** - Comprehensive test suite
- **setup_and_test.py** - Interactive setup tool

### Online Resources:
- **OpenRouter**: https://openrouter.ai/
- **OpenRouter Models**: https://openrouter.ai/models
- **OpenRouter Docs**: https://openrouter.ai/docs
- **Supabase Auth**: https://supabase.com/docs/guides/auth

---

## ✨ What's Been Changed

### Modified Files:
1. ✅ `app/core/config.py` - Added OpenRouter support
2. ✅ `app/core/llm.py` - Integrated OpenRouter provider
3. ✅ `.env.example` - Updated with OpenRouter config
4. ✅ `.env` - Created from template (needs your values!)

### New Files:
1. ✅ `test_all_endpoints.py` - Full test suite
2. ✅ `check_config.py` - Config validator
3. ✅ `setup_and_test.py` - Interactive setup
4. ✅ Documentation files

---

## 🎉 Ready to Test!

Follow these steps in order:

```bash
# 1. Configure .env file
notepad .env

# 2. Check configuration
python check_config.py

# 3. Start server (Terminal 1)
uvicorn app.main:app --reload --port 8000

# 4. Run tests (Terminal 2)
python test_all_endpoints.py

# 5. Check results
notepad test_report.json
```

That's it! Your Career Intelligence Backend is configured with OpenRouter and ready for comprehensive testing! 🚀

---

**Need Help?**
- Check `test_report.json` for detailed logs
- Review the documentation files listed above
- Verify `.env` configuration with `python check_config.py`

**Happy Testing!** 🎯
