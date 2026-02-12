# Security Update: Rate Limiting & Input Sanitization

## Features Added

### 1. Rate Limiting (SlowAPI)
Rate limits have been applied to all major API endpoints to prevent abuse and manage load.

- **Standard Read Endpoints**: 60 requests/minute
  - Applied to `GET` endpoints for Students, Recruiters, and Admin (e.g., fetching profiles, skills, stats).
- **Write Operations**: 30 requests/minute
  - Applied to `POST`, `PATCH`, `DELETE` endpoints (e.g., updating profile, adding skills).
- **AI/LLM Endpoints**: 10 requests/hour & 3 requests/minute
  - Key cost-control measure for `app/api/ai.py` routes (`/career-advice`, `/interview-prep`, etc.).
- **Recruiter Search**: 100 requests/minute
  - Allows higher throughput for candidate browsing but prevents scraping.
- **Admin Actions**: 30 requests/minute
  - Applied to sensitive operations like recomputing scores.

### 2. LLM Input Sanitization
Integrated `app/security/llm_security.py` into `app/api/ai.py`.

- **HTML/Script Stripping**: User inputs are sanitized using `bleach` to remove potential XSS vectors before processing (though mainly relevant for prompt safety here).
- **Prompt Injection Defense**: Inputs are scanned for common injection patterns (e.g., "Ignore all previous instructions") before being sent to the LLM.
- **Whitespace Normalization**: Ensures cleaner input for the model.

## Modified Files
- `app/api/students.py`
- `app/api/events.py`
- `app/api/ai.py`
- `app/api/recruiters.py`
- `app/api/admin.py`

## Configuration
Rate limiting uses Redis if `REDIS_URL` is configured in `.env`. Otherwise, it falls back to in-memory storage (not recommended for production).
