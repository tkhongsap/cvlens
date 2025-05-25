# CVLens-Agent— PRD v1.3

## Project Objective
Deliver a **personal, desktop‑only** agent that streamlines early‑stage hiring by automatically collecting résumés from a *single, user‑selected Outlook folder*, extracting relevant data, scoring each candidate, and presenting an interactive shortlist so the hiring manager can decide "Interview" or "Pass" in seconds.

## Executive Summary
CVLens targets a recurring time‑sink in the recruitment process: downloading and reviewing attachments buried in email threads. By combining Microsoft Graph for targeted mail access with open‑source parsing and NLP libraries, the app brings every résumé into a unified dashboard while ensuring all processing stays **local** to the user's machine. The MVP is intentionally scoped to a two‑day build: folder‑scoped email sync, PDF/DOC parsing, rule‑based scoring against a YAML job profile, and a Streamlit UI with one‑click decisions and CSV export. The result is a privacy‑first proof‑of‑concept that can later evolve into a full ATS module.

---

### 1 · Purpose & Success Criteria
| Objective                               | Metric                                                                                      |
| --------------------------------------- | ------------------------------------------------------------------------------------------- |
| **Retrieve & cache résumés** [MVP‑core] | 100 % of messages **in the selected folder only** downloaded & logged                       |
| **Parse + score** [MVP‑core]            | ≥ 95 % of PDF/DOC/DOCX parsed; each candidate gets 0‑100 match score                        |
| **Actionable dashboard** [MVP‑core]     | List view loads < 2 s, sortable by score; one‑click **Interested** / **Pass** updates state |
| **Resilience** [MVP‑core]               | Interrupted run can restart without duplicate processing                                    |
| **Local‑only privacy** [MVP‑core]       | No résumé content leaves laptop; *Purge Data* button wipes cache + DB                       |

---

### 2 · User Journey (condensed)
1. **Launch** `run_local.bat` → Streamlit opens.  
2. **Authenticate** (device‑code flow) and pick a folder (e.g., *Recruitment*).  
3. **Click Sync** → progress bar for retrieval → parsing → scoring.  
4. **Review dashboard** once candidates load.  
5. **Mark Interested/Pass**, add optional note or tag.  
6. **Export CSV** or **Purge Data** when finished.  

---

### 3 · Functional Requirements
| ID   | Requirement                                                                                              | Tag      |
| ---- | -------------------------------------------------------------------------------------------------------- | -------- |
| F‑1  | OAuth via Graph `Mail.Read` **delegated** scope.                                                         | MVP‑core |
| F‑2  | Folder picker; chosen `folder_id` stored in `settings.json`.                                             | MVP‑core |
| F‑3  | All subsequent Graph calls must prefix the stored `folder_id`; optional toggle to include child folders. | MVP‑core |
| F‑4  | Manual **Sync** button + optional auto‑poll (5‑60 min).                                                  | MVP‑core |
| F‑5  | Download attachments; skip > 25 MB with warning.                                                         | MVP‑core |
| F‑6  | Convert PDF/DOC/DOCX to text; OCR fallback for scans.                                                    | MVP‑core |
| F‑7  | Extract entities (name, email, phone, skills, edu, exp).                                                 | MVP‑core |
| F‑8  | Score via TF‑IDF vs. `job_profile.yml` (weights 60/20/20).                                               | MVP‑core |
| F‑9  | Persist to AES‑encrypted SQLite DB.                                                                      | MVP‑core |
| F‑10 | Dashboard list: Name, Score, Date, Tags, Decision.                                                       | MVP‑core |
| F‑11 | Candidate detail drawer with résumé preview & "Why this score".                                         | MVP‑core |
| F‑12 | **Interested / Pass / Undo** actions; duplicate prevention.                                              | MVP‑core |
| F‑13 | Clear error banners + downloadable log.                                                                  | MVP‑core |
| F‑14 | Progress indicators for each pipeline stage.                                                             | MVP‑core |
| F‑15 | Duplicate detection via SHA‑256 hash.                                                                    | MVP‑core |
| F‑16 | Data‑retention auto‑purge (> 30 days).                                                                   | Stretch  |
| F‑17 | Search box over résumé text.                                                                             | Stretch  |
| F‑18 | Candidate notes & custom tags.                                                                           | Stretch  |
| F‑19 | Batch actions (multi‑select).                                                                            | Stretch  |

---

### 4 · Non‑Functional Requirements
| Category      | NFR                                                       |
| ------------- | --------------------------------------------------------- |
| Performance   | ≤ 5 s parse + score per résumé on 4‑core machine          |
| Resilience    | Pipeline resumes safely after crash; idempotent sync      |
| Privacy       | All queries folder‑scoped; AES‑encrypted DB; Purge button |
| UX            | Skeleton loaders, empty states, keyboard nav              |
| Accessibility | WCAG 2.1 AA basics                                        |
| Logging       | Rotating file logs; DEBUG toggle in UI                    |

---

### 5 · Edge‑case Handling
- **Large attachments > 25 MB** → skip + warn.  
- **Non‑English résumés** → tag `language_unknown`; still display.  
- **HTTP 429 rate‑limit** → exponential back‑off (max 3 retries).  
- **Duplicate emails** → skip via message‑ID check.  

---

### 6 · Architecture Snapshot
```text
┌─Streamlit UI────────────────────┐
│ Folder picker / Sync button     │
│ List → Detail drawer            │
└─────────▲───────────▲───────────┘
          │SQLite (AES)│
┌─────────┴───────────┴───────────┐
│   Domain Service Layer          │
│ ingest.py  parse.py  score.py   │
└─────────▲───────────▲───────────┘
          │O365 SDK   │File I/O
          │           │
      Microsoft Graph API (folder‑scoped)
```

---

### 7 · Day‑0 Deliverables
| Artefact                | Notes                                       |
| ----------------------- | ------------------------------------------- |
| `README.md`             | setup, device‑code auth, troubleshooting    |
| `.env.example`          | CLIENT_ID, TENANT_ID, AES_KEY               |
| `run_local.bat` / `.sh` | one‑click launcher                          |
| `settings.json`         | folder_id, poll_interval, retention_days    |
| `tests/`                | unit + integration (≥ 80 % core)            |
| `log/hiresift.log`      | rotating logs                               |
| Sample résumés          | 3 files for smoke test                      |

---

### 8 · Sprint Plan (48 hrs)
| When         | Task                                            |
| ------------ | ----------------------------------------------- |
| **Day 1 AM** | Repo scaffold, OAuth helper, folder picker      |
| **Day 1 PM** | Attachment download + dedupe, text extraction   |
| **Day 2 AM** | Scoring algorithm, SQLite model, decision logic |
| **Day 2 PM** | Streamlit UI, encryption, smoke tests, demo     |

---

### 9 · Risks & Mitigations
| Risk          | Mitigation                          |
| ------------- | ----------------------------------- |
| OAuth hurdles | Device‑code helper script           |
| OCR slowness  | Only OCR low‑text PDFs; async queue |
| Time‑box      | Stretch items slip first            |

---

*Document v1.3 — Project Objective, Executive Summary, folder‑scope confirmed.*