# Career Intelligence Backend - Testing Configuration

## Environment Setup for Testing

### Required Variables in .env

```bash
# Supabase Configuration (Required)
SUPABASE_URL=your-supabase-project-url
SUPABASE_KEY=your-supabase-service-role-key
SUPABASE_JWT_SECRET=your-supabase-jwt-secret

# Scoring Configuration
SCORING_VERSION=v1.0
EVENT_WINDOW_DAYS=90
DECAY_HALF_LIFE_DAYS=30

# LLM Configuration - OpenRouter (Required for AI endpoints)
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Alternative LLM Providers (Optional)
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
GOOGLE_API_KEY=your-google-api-key
GOOGLE_MODEL=gemini-2.0-flash

# Security Settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
REDIS_URL=redis://localhost:6379
JWT_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Testing Configuration
TEST_BASE_URL=http://localhost:8000
TEST_STUDENT_TOKEN=your-student-jwt-token
TEST_RECRUITER_TOKEN=your-recruiter-jwt-token
TEST_ADMIN_TOKEN=your-admin-jwt-token
```

## How to Get Test Tokens

### Option 1: Using Supabase Dashboard

1. Go to your Supabase project dashboard
2. Navigate to Authentication > Users
3. Create test users with different roles
4. Get JWT tokens for each user

### Option 2: Using Supabase Auth API

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

The response will contain an `access_token` field - use this as your TEST_STUDENT_TOKEN.

Repeat for recruiter and admin users with appropriate roles.

## OpenRouter API Key

1. Visit https://openrouter.ai/
2. Sign up or log in
3. Navigate to Keys section
4. Create a new API key
5. Add it to your .env as OPENROUTER_API_KEY

## Running Tests

1. Ensure your backend server is running:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

2. In a separate terminal, run the test script:
   ```bash
   python test_all_endpoints.py
   ```

## Expected Output

The test script will:
- Test all system endpoints (health, root)
- Test student CRUD operations (profile, skills, education, experience, projects, certifications)
- Test event emission and retrieval
- Test all AI endpoints with OpenRouter (profile analysis, career advice, interview prep, skill gaps, resume suggestions)
- Test recruiter endpoints (candidate search, profiles, timelines)
- Test admin endpoints (scoring, debugging, recomputation)
- Generate a detailed JSON report (`test_report.json`)

## Troubleshooting

### No tokens available
- Tests requiring authentication will be skipped
- You'll see yellow "⊘" markers for skipped tests

### 401 Unauthorized
- Check that your JWT tokens are valid
- Tokens expire - generate fresh ones if needed

### 500 Internal Server Error on AI endpoints
- Verify OPENROUTER_API_KEY is set correctly
- Check that you have credits on your OpenRouter account
- Ensure LLM_PROVIDER=openrouter in .env

### Connection refused
- Ensure the backend server is running
- Check TEST_BASE_URL matches your server address

## Test Report

After running, check `test_report.json` for:
- Detailed request/response logs
- Timestamps for each test
- Full error messages
- Response data from successful calls

This is invaluable for debugging failing tests.
