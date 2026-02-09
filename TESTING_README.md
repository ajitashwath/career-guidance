# API Testing Guide - Quick Start

## 🚀 Quick Setup

We've configured the backend to use **OpenRouter** for AI features. Follow these steps to test all endpoints:

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Set Up Environment Variables

1. Create a `.env` file from the example:
   ```bash
   copy .env.example .env  # Windows
   # or
   cp .env.example .env    # Linux/Mac
   ```

2. Edit `.env` and configure these **required** variables:
   ```bash
   # Supabase Configuration
   SUPABASE_URL=your-supabase-project-url
   SUPABASE_KEY=your-supabase-service-role-key
   SUPABASE_JWT_SECRET=your-supabase-jwt-secret
   
   # OpenRouter for AI (IMPORTANT!)
   LLM_PROVIDER=openrouter
   OPENROUTER_API_KEY=your-openrouter-api-key
   OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
   ```

3. **Optional** - Add test tokens for comprehensive testing:
   ```bash
   TEST_STUDENT_TOKEN=your-student-jwt-token
   TEST_RECRUITER_TOKEN=your-recruiter-jwt-token
   TEST_ADMIN_TOKEN=your-admin-jwt-token
   ```

### Step 3: Get OpenRouter API Key

1. Visit https://openrouter.ai/
2. Sign up or log in
3. Go to **Keys** section
4. Create a new API key
5. Add it to `.env` as `OPENROUTER_API_KEY`

### Step 4: Start the Server

```bash
uvicorn app.main:app --reload --port 8000
```

The server will start at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- OpenAPI spec: `http://localhost:8000/openapi.json`

### Step 5: Run Tests

In a **separate terminal**, run:

```bash
python test_all_endpoints.py
```

## 📋 What Gets Tested

The comprehensive test suite covers:

### ✅ System Endpoints
- `GET /health` - Health check
- `GET /` - Root endpoint

### 👨‍🎓 Student Endpoints
- `GET /students/me` - Get profile
- `PATCH /students/me` - Update profile
- `GET/POST/PATCH/DELETE /students/me/skills` - Manage skills
- `GET/POST/PATCH/DELETE /students/me/education` - Manage education
- `GET/POST/PATCH/DELETE /students/me/experience` - Manage experience
- `GET/POST/PATCH/DELETE /students/me/projects` - Manage projects
- `GET/POST/PATCH/DELETE /students/me/certifications` - Manage certifications

### 📊 Event Endpoints
- `GET /events/types` - List event types
- `POST /events` - Emit event (triggers scoring)

### 🤖 AI Endpoints (Using OpenRouter!)
- `GET /ai/profile-analysis` - AI profile analysis
- `POST /ai/career-advice` - Personalized career advice
- `POST /ai/interview-prep` - Generate interview questions
- `POST /ai/skill-gaps` - Skill gap analysis
- `GET /ai/resume-suggestions` - Resume improvement suggestions

### 🏢 Recruiter Endpoints
- `GET /recruiters/candidates` - Search candidates
- `GET /recruiters/candidates/{id}` - Get candidate profile
- `GET /recruiters/candidates/{id}/summary` - Intelligence summary
- `GET /recruiters/candidates/{id}/timeline` - Activity timeline

### 🔧 Admin Endpoints
- `GET /admin/scoring/version` - Scoring configuration
- `GET /admin/system/stats` - System statistics
- `GET /admin/users/{id}/events` - Raw event stream
- `GET /admin/scoring/debug/{id}` - Scoring debug info
- `POST /admin/users/{id}/recompute` - Force score recomputation

## 🎯 Interactive Setup Tool

For an interactive setup experience, use:

```bash
python setup_and_test.py
```

This will guide you through:
1. Checking prerequisites
2. Setting up `.env`
3. Installing dependencies
4. Validating configuration
5. Starting the server
6. Running tests

## 📊 Test Output

The test script provides:

### Console Output
- ✅ **Green checkmarks** for passed tests
- ❌ **Red X's** for failed tests
- ⊘ **Yellow symbols** for skipped tests (missing auth)

### Detailed Report
After running, check `test_report.json` for:
- Full request/response data
- Timestamps for each test
- Error messages and stack traces
- AI-generated responses (for debugging)

### Example Output
```
================================================================================
                     System Endpoints
================================================================================

✓ GET /health: Status: healthy
✓ GET /: Name: Career Intelligence API, Version: 1.0.0

================================================================================
                     AI Endpoints (OpenRouter)
================================================================================

Testing AI Profile Analysis...
✓ GET /ai/profile-analysis: Analysis completed

Testing AI Career Advice...
✓ POST /ai/career-advice: Advice generated

Testing AI Interview Preparation...
✓ POST /ai/interview-prep: Interview questions generated

================================================================================
                          TEST SUMMARY
================================================================================
  Total Tests:    45
  ✓ Passed:       42
  ✗ Failed:       0
  ⊘ Skipped:      3
  
  Pass Rate:      100.0%
```

## 🔑 Getting Test Tokens

### Using Supabase Auth API

```bash
# Sign up a test user
curl -X POST 'https://your-project.supabase.co/auth/v1/signup' \
  -H "apikey: your-anon-key" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@test.com",
    "password": "testpassword123",
    "data": {
      "role": "student",
      "full_name": "Test Student"
    }
  }'

# Login to get JWT token
curl -X POST 'https://your-project.supabase.co/auth/v1/token?grant_type=password' \
  -H "apikey: your-anon-key" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@test.com",
    "password": "testpassword123"
  }'
```

Use the `access_token` from the response as your `TEST_STUDENT_TOKEN`.

## 🐛 Troubleshooting

### AI endpoints return 500 errors
- ✅ Check `OPENROUTER_API_KEY` is set correctly in `.env`
- ✅ Verify you have credits on OpenRouter
- ✅ Ensure `LLM_PROVIDER=openrouter` in `.env`

### 401 Unauthorized errors
- ✅ Generate fresh JWT tokens (they expire)
- ✅ Verify token format in `.env`: `Bearer token` not needed, just the token

### Connection refused
- ✅ Ensure server is running: `uvicorn app.main:app --reload --port 8000`
- ✅ Check `TEST_BASE_URL` in `.env` matches your server

### Tests are skipped
- Tests without auth tokens will be skipped
- This is expected - configure tokens to run all tests

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs (when server is running)
- **OpenRouter Docs**: https://openrouter.ai/docs
- **Supabase Auth**: https://supabase.com/docs/guides/auth
- **Detailed Testing Guide**: See `TESTING_GUIDE.md`

## ✨ What's New

### OpenRouter Integration
We've configured the backend to use **OpenRouter** which provides:
- Access to multiple AI models (Claude, GPT-4, Gemini, etc.)
- Unified API across providers
- Cost-effective pricing
- Better rate limits

The default model is `anthropic/claude-3.5-sonnet` but you can change it in `.env` by setting `OPENROUTER_MODEL`.

Available models on OpenRouter:
- `anthropic/claude-3.5-sonnet` (recommended)
- `openai/gpt-4o`
- `google/gemini-2.0-flash-exp`
- And many more!

## 🎉 Happy Testing!

If you encounter any issues, check:
1. `test_report.json` for detailed error logs
2. Server logs in the terminal running uvicorn
3. Your `.env` configuration

For questions, refer to `TESTING_GUIDE.md` or the main `README.md`.
