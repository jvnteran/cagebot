# CAGEBOT — Autonomous UFC Fight Prediction Engine

[![CI](https://github.com/jvnteran/cagebot/actions/workflows/ci.yml/badge.svg)](https://github.com/jvnteran/cagebot/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Live-dc2626.svg)](https://cagebot.streamlit.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An end-to-end machine learning system that predicts UFC fight outcomes, running autonomously in production since December 2025.

**68% combined accuracy** across 225 decided fights (18 events) — XGBoost model with human-in-the-loop override layer.

[Live Dashboard](https://cagebot.streamlit.app) · [Architecture](#architecture) · [Database Schema](#database-schema) · [Model Evaluation](#model-evaluation)

---

## Results

| Metric | Value |
|--------|-------|
| Combined accuracy (model + overrides) | **68.0%** (153/225) |
| Model-only accuracy | 63.6% (143/225) |
| Founder override record | 81.3% (13/16) |
| Events completed | 18 |
| Prediction period | Dec 2025 — May 2026 |
| Model | XGBoost V2.4, 154 features |

The override system applies scenario-based reasoning to select fights where the model's statistical view misses contextual factors — proving that combining ML with domain expertise outperforms either approach alone.

---

## Architecture

```mermaid
graph TB
    subgraph Data Ingestion
        A[TheOddsAPI<br/>5 sportsbooks] --> D[Feature Engineering]
        B[UFCStats<br/>fight history] --> D
        C[ESPN Profiles<br/>career context] --> D
        E[ELO System<br/>custom ratings] --> D
    end

    subgraph Prediction
        D --> F[XGBoost V2.4<br/>154 features]
        F --> G[Method of Victory<br/>KO/SUB/DEC probs]
        F --> H[Founder Overrides<br/>scenario elimination]
    end

    subgraph Automation
        I[Phase-Aware Scheduler] --> J[Pre-Event Pipeline<br/>10 steps]
        I --> K[Post-Event Pipeline<br/>8 steps]
        I --> L[6 Autonomous Agents]
    end

    subgraph Analytics
        M[(PostgreSQL<br/>6 tables, 4 views)] --> N[Streamlit Dashboard<br/>6 pages]
        O[ETL Loader] --> M
    end

    H --> O
    K --> O
```

---

## Database Schema

Normalized PostgreSQL schema (3NF) — chosen over star schema because the system is operational, not warehouse-analytical. At ~250 rows, JOINs execute in <1ms.

```mermaid
erDiagram
    events ||--o{ fights : contains
    fighters ||--o{ fights : "fighter_a"
    fighters ||--o{ fights : "fighter_b"
    fighters ||--o{ fights : "model_pick"
    fighters ||--o{ fights : "actual_winner"
    fights ||--o{ odds_snapshots : has
    fights ||--o| overrides : has
    fighters ||--o{ fighter_elo_history : tracks

    events {
        int id PK
        varchar stem UK
        varchar name
        date date
        varchar status
        varchar venue
        varchar city
        varchar country
        decimal latitude
        decimal longitude
    }

    fighters {
        int id PK
        varchar name UK
        varchar stance
        decimal height_in
        decimal reach_in
        date dob
    }

    fights {
        int id PK
        int event_id FK
        int fighter_a_id FK
        int fighter_b_id FK
        int model_pick_id FK
        decimal model_prob
        varchar predicted_method
        decimal ko_prob
        decimal sub_prob
        decimal dec_prob
        int actual_winner_id FK
        varchar finish_method
        int finish_round
    }

    odds_snapshots {
        int id PK
        int fight_id FK
        varchar bookmaker
        decimal odds
        decimal implied_pct
        varchar snapshot_type
        timestamp captured_at
    }

    overrides {
        int id PK
        int fight_id FK
        int override_pick_id FK
        text notes
    }

    fighter_elo_history {
        int id PK
        int fighter_id FK
        date event_date
        decimal elo_before
        decimal elo_after
        decimal elo_delta
        varchar opponent_name
        varchar result
    }
```

### Design Decisions

| Decision | Chosen | Why |
|----------|--------|-----|
| 3NF over star schema | Normalized tables | Operational write patterns, tiny data, JOINs are instant |
| Views over stored aggregates | Computed on read | <1ms queries, eliminates sync bugs |
| Analytical layer (not migration) | Separate from pipeline | Zero production risk, standard data engineering pattern |
| ELO history without FK to events | Direct date column | 8,498 rows across 600+ historical events can't reference 20-row events table |

---

## Model Evaluation

| Metric | Value | Meaning |
|--------|-------|---------|
| AUC | ~0.68 | Discrimination ability (0.5 = random, 1.0 = perfect) |
| Brier Score | ~0.22 | Calibration quality (0.0 = perfect, 0.25 = coin flip) |
| Sample Size | 225 | Decided fights across 18 events |

The dashboard includes a full [Model Evaluation page](https://cagebot.streamlit.app) with calibration curve, accuracy-by-confidence analysis, and prediction distribution.

---

## Pipelines

The system runs two automated pipelines on a VPS cron schedule:

**Pre-Event (Monday)** — 10 steps:
1. Rebuild fighter state (ELO + recency from fightlogs)
2. Fetch multibook odds from TheOddsAPI (5 sportsbooks)
3. Run XGBoost V2.4 predictions (aborts if no odds)
4. Scrape ESPN fighter profiles for context
5. Run intuition agent (Claude-powered scenario analysis)
6. Run risk assessment on each prediction
7. Append assessment to master records
8. Ingest picks to master_picks.csv (atomic, idempotent)
9. Ingest to Excel workbook
10. Post picks card to Discord

**Post-Event (Sunday)** — 8 steps:
1. Fetch + cache UFCStats HTML
2. Parse results with completeness gate (retries if incomplete)
3. Update master_picks.csv with actual outcomes (atomic write)
4. Generate missed picks analysis
5. Rebuild fighter state with new ELO ratings
6. Run post-event agent (Claude-powered miss analysis)
7. Update master_events.csv (accuracy metrics)
8. Post results card to Discord

See [`pipelines/`](pipelines/) for the sanitized pipeline code.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| ML Model | XGBoost (Python, scikit-learn) |
| Database | PostgreSQL 16 (Docker, Neon.tech) |
| ETL | Python (psycopg2, pandas, idempotent upserts) |
| Dashboard | Streamlit + Plotly |
| Automation | Phase-aware cron scheduler on DigitalOcean VPS |
| Data Sources | TheOddsAPI, UFCStats, ESPN |
| CI/CD | Pre-commit hooks (ruff, pytest) |

---

## Dashboard Pages

| Page | What it shows |
|------|---------------|
| **Overview** | Headline metrics, accuracy trend (per-event + cumulative), best contrarian calls, project story |
| **Locations** | World map with accuracy by venue city |
| **Fighters** | Fighter search with full-career ELO trajectory chart |
| **Fights** | Filterable table of all 225 predictions with donut chart |
| **SQL Explorer** | 6 pre-built queries with visible SQL and live results |
| **Model Evaluation** | Calibration curve, AUC, Brier score, confidence analysis |

---

## Quick Start

```bash
# Start PostgreSQL locally
docker compose up -d

# Load data (requires CSV source files)
DATABASE_URL=postgresql://cagebot:cagebot_dev@localhost:5432/cagebot \
  python etl/load_all.py

# Run dashboard
cd dashboard
streamlit run Overview.py
```

---

## Project Structure

```
cagebot/
├── .github/workflows/ci.yml        # GitHub Actions: lint + test on push
├── Dockerfile                       # Container deployment for dashboard
├── Makefile                         # make test, make lint, make run
├── LICENSE                          # MIT
├── schema/
│   ├── 001_create_tables.sql        # 6 tables with constraints + indexes
│   └── 002_create_views.sql         # 4 analytical views
├── etl/
│   ├── load_all.py                  # Orchestrator (FK-order loading)
│   ├── load_fighters.py             # Name normalization + physical attributes
│   ├── load_events.py               # Venue backfill from lookup CSV
│   ├── load_fights.py               # MOV enrichment + fight name matching
│   ├── load_odds.py                 # Column-to-row pivot (opening/closing)
│   ├── load_overrides.py            # Override filter + name resolution
│   └── load_elo_history.py          # 8,498 career ELO rows
├── pipelines/
│   ├── pre_event.py                 # 10-step pre-event pipeline
│   └── post_event.py                # 8-step post-event pipeline
├── dashboard/
│   ├── Overview.py                    # Overview page
│   ├── pages/                       # 5 additional pages
│   └── components/                  # DB connection, styles, query definitions
├── tests/unit/                      # 16 ETL unit tests
├── docker-compose.yml               # PostgreSQL + pgAdmin
└── .env.example                     # Required environment variables
```

---

Built by [Juan Vicente Navas Teran](https://github.com/jvnteran)
