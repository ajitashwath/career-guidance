# AI Career Intelligence - Backend

Event-driven backend for an AI-powered career intelligence platform that tracks user actions, derives behavioral intelligence scores, and serves students, recruiters, and universities with role-based access.

## Quick Start

### Prerequisites
- Python 3.11+
- Supabase account with the schema applied
- Docker (optional)

### Local Development

1. **Clone and setup:**
   ```bash
   cd career-intelligence
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   copy .env.example .env
   # Edit .env with your Supabase credentials
   ```

3. **Run the server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

4. **Access API docs:** http://localhost:8000/docs

### Docker

```bash
docker-compose up --build
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                             │
│  Students │ Recruiters │ Admins (JWT Auth via Supabase)     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   FastAPI Gateway                            │
│  /students/* │ /events │ /recruiters/* │ /admin/*           │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Intelligence Pipeline                           │
│  Event Ingestion → Decay → Aggregation → Snapshot           │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                 Supabase (Postgres)                          │
│  user_profiles │ user_events │ user_intelligence_snapshots  │
└─────────────────────────────────────────────────────────────┘
```

## Intelligence Scoring

### Dimensions (0-100 each)
| Score | Weight | Signals |
|-------|--------|---------|
| Engagement | 15% | Profile updates, skill additions, platform activity |
| Learning Velocity | 20% | Course completions, skill verifications, assessments |
| Commitment | 20% | Streaks, goal completion, application follow-through |
| Interview Readiness | 25% | Mock interviews, practice sessions, feedback |
| Professional Maturity | 20% | Recommendations, community contributions, mentorship |

### Tier Assignment
- **Tier 1**: Overall score ≥ 80 (Top performers)
- **Tier 2**: 40 ≤ score < 80 (Average)
- **Tier 3**: score < 40 (Needs development)

## Security

- JWT authentication via Supabase Auth
- Role-based access control (Student, Recruiter, Admin)
- Row Level Security (RLS) on Postgres
- Recruiters never see raw events or private data
- Students cannot see internal tier labels

## Project Structure

```
app/
├── main.py              # FastAPI entry point
├── core/
│   ├── config.py        # Settings from environment
│   └── auth.py          # JWT validation & RBAC
├── api/
│   ├── students.py      # Student profile & entity CRUD
│   ├── events.py        # Event ingestion
│   ├── recruiters.py    # Candidate search & views
│   └── admin.py         # Debug & recomputation
├── intelligence/
│   ├── scoring.py       # Main scoring engine
│   ├── decay.py         # Time-based decay functions
│   └── aggregators.py   # Dimension score calculators
├── workers/
│   └── recompute_scores.py  # Background processing
├── db/
│   ├── supabase.py      # Database client
│   └── queries.py       # SQL constants
└── schemas/
    ├── profiles.py      # Profile Pydantic models
    ├── events.py        # Event types & models
    └── intelligence.py  # Score & snapshot models
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | Required |
| `SUPABASE_KEY` | Service role key | Required |
| `SUPABASE_JWT_SECRET` | JWT secret | Required |
| `SCORING_VERSION` | Version tag for snapshots | v1.0 |
| `EVENT_WINDOW_DAYS` | Days of events to analyze | 90 |
| `DECAY_HALF_LIFE_DAYS` | Exponential decay half-life | 30 |

## API Reference

### Students
- `GET /students/me` - Get own profile
- `PATCH /students/me` - Update profile
- `GET/POST/DELETE /students/me/skills` - Manage skills
- `GET/POST/DELETE /students/me/education` - Manage education
- `GET/POST/DELETE /students/me/experience` - Manage experience
- `GET/POST/DELETE /students/me/projects` - Manage projects
- `GET/POST/DELETE /students/me/certifications` - Manage certifications

### Events
- `POST /events` - Emit event (triggers score recomputation)
- `GET /events/types` - List valid event types

### Recruiters
- `GET /recruiters/candidates` - Search candidates with filters
- `GET /recruiters/candidates/{id}` - Get candidate profile
- `GET /recruiters/candidates/{id}/summary` - Intelligence summary
- `GET /recruiters/candidates/{id}/timeline` - Activity timeline

### Admin
- `POST /admin/users/{id}/recompute` - Force recomputation
- `GET /admin/users/{id}/events` - View raw events
- `GET /admin/scoring/debug/{id}` - Debug score breakdown
- `GET /admin/scoring/version` - View scoring config

## Testing

```bash
pytest tests/ -v
```

## 📜 License

MIT
