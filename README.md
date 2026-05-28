# AutoSOC

An autonomous Security Operations Center powered by Claude. AutoSOC ingests raw security alerts and logs, runs them through a 4-stage AI agent pipeline, and produces structured triage decisions, attack investigations, response action plans, and full incident reports — all without human intervention.

## How It Works

```
Raw Log / Alert
      ↓
  Triage Agent      → classify threat, assign priority (P0–P4), extract indicators
      ↓
Investigation Agent → identify attack pattern, MITRE tactics, blast radius, timeline
      ↓
  Response Agent    → generate immediate / short-term / long-term action plans
      ↓
   Report Agent     → produce executive summary + full technical incident report
      ↓
   PostgreSQL DB    → store all findings
      ↓
   React Dashboard  → browse, filter, and review incidents
```

Each agent is powered by **Claude** via CrewAI and returns a validated Pydantic schema, so every stage has a guaranteed structure that feeds cleanly into the next.

## Stack

| Layer | Technology |
|-------|-----------|
| AI Agents | CrewAI + Claude (claude-sonnet-4-20250514) |
| Backend API | Python + FastAPI + Uvicorn |
| Database | PostgreSQL (Neon serverless) + SQLAlchemy |
| Frontend | React 19 + Vite + Tailwind CSS 4 |

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- A Neon (or any PostgreSQL) database
- Anthropic API key

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create `backend/.env`:
```
NEON_CONNECTION_STRING=postgresql://user:password@host/dbname
ANTHROPIC_API_KEY=sk-ant-...
```

```bash
uvicorn main:app --reload
# API available at http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# UI available at http://localhost:5173
```

## API Reference

All endpoints are prefixed with `/api`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analyse` | Submit a raw log string; runs full pipeline and returns all findings |
| `GET` | `/incidents` | List all incidents |
| `GET` | `/incidents/{id}` | Get a single incident |
| `GET` | `/incidents/{id}/findings` | Get all agent findings for an incident |
| `GET` | `/incidents/{id}/report` | Get the generated incident report |
| `GET` | `/incidents/priority/{priority}` | Filter incidents by priority (p0–p4) |
| `GET` | `/stats` | Dashboard statistics (counts by status and priority) |

**Submit an alert:**
```bash
curl -X POST http://localhost:8000/api/analyse \
  -H "Content-Type: application/json" \
  -d '{"raw_log": "Failed SSH login from 192.168.1.50 — 47 attempts in 2 minutes", "source": "manual"}'
```

## Priority Levels

| Priority | Meaning |
|----------|---------|
| P0 | Active breach — immediate response required |
| P1 | Critical threat |
| P2 | High severity |
| P3 | Medium severity |
| P4 | Informational |

Confidence <60% automatically flags the incident for human review. P0/P1 or a "critical" blast radius automatically sets the escalation flag.

## Project Structure

```
AutoSOC/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── orchestrator.py      # Runs the 4-agent pipeline
│   ├── agents/              # Triage, investigation, response, report agents
│   ├── api/routes.py        # REST endpoints
│   ├── db/database.py       # SQLAlchemy models
│   ├── models/schemas.py    # Pydantic schemas
│   └── tools/               # Placeholder: VirusTotal, log parser
└── frontend/
    └── src/
        ├── pages/           # Dashboard, Analyse, Incidents, Incident detail
        ├── components/      # Sidebar
        └── services/api.js  # Backend API client
```

## Roadmap

- [ ] VirusTotal integration for hash/IP lookups (`backend/tools/virustotal.py`)
- [ ] Structured log parser for Windows Event Logs, syslog, CEF (`backend/tools/log_parser.py`)
- [ ] SIEM webhook ingestion (Splunk, Elastic, Sentinel)
- [x] PDF report export (jsPDF, frontend-only)
- [ ] CSV export
- [ ] Authentication and multi-user support
- [ ] Scheduled / automated ingestion jobs

## License

See [LICENSE](LICENSE).
