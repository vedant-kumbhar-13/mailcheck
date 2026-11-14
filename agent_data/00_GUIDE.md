# MailCheck — Claude Code Prompt Guide

> **Project path (Windows):** `P:\mail_validator`
> **Platform:** antygravity (Claude Sonnet 4.6 Thinking / Claude Opus 4.6 Thinking)
> **Architecture version:** v2.0 (2026-11-14)

---

## How to use these prompts

Each `C0_` to `C7_` file is a **standalone prompt** you paste into Claude Code (antygravity chat) for that chunk. You do **not** paste all of them at once. Work one chunk at a time, finish its exit gate, then move to the next.

### Step-by-step workflow

```
1. Open P:\mail_validator in VS Code (or your editor).
2. Open antygravity chat in the same window.
3. Paste the prompt for C0 → let the model generate all files.
4. Review, run the tests listed at the bottom of the prompt.
5. All tests green? Tick the exit gate. Commit. Move to C1.
```

### Which model per chunk

| Chunk | Recommended model | Reason |
|-------|-------------------|--------|
| C0 Foundation | Claude Sonnet 4.6 Thinking | Config and boilerplate |
| C1 Validation core | Claude Sonnet 4.6 Thinking | Algorithmic logic |
| C2 Single API + UI | Claude Sonnet 4.6 Thinking | CRUD endpoints |
| C3 Bulk engine | **Claude Opus 4.6 Thinking** | Complex async concurrency |
| C4 Bulk UI | Claude Sonnet 4.6 Thinking | React components |
| C5 Privacy + hardening | Claude Sonnet 4.6 Thinking | Security rules |
| C6 Deploy | Claude Sonnet 4.6 Thinking | Docker + CI |
| C7 Load test + release | Claude Sonnet 4.6 Thinking | Locust scripts |

---

## Steps YOU must do manually (no AI can do these)

Mark each with ✅ when done.

| # | When | What | Where |
|---|------|------|-------|
| M1 | Before C0 | Create a **public** GitHub repository named `mail-validator` | github.com → New repository |
| M2 | Before C0 | Install Python 3.12, Node 20 LTS, Git on your machine | python.org, nodejs.org |
| M3 | Before C0 | Run `git init` and connect to GitHub remote | PowerShell in `P:\mail_validator` |
| M4 | Before C6 | Create a free account at **render.com** (no card needed) | render.com |
| M5 | C6 | In Render dashboard: New → Web Service → connect GitHub repo | Render dashboard |
| M6 | C6 | Set the 7 environment variables in Render dashboard | Render → Environment tab |
| M7 | C6 | Copy the Render app URL and set `ALLOW_ORIGINS` env var | Render → Environment tab |
| M8 | C7 | (Optional) Add a custom domain in Render | Render → Settings → Custom Domain |

---

## Environment variables reference

Set these in Render dashboard (M6 above) and locally in a `.env` file (never commit `.env`).

```
ALLOW_ORIGINS=https://your-app.onrender.com
MAX_CSV_BYTES=2097152
MAX_CSV_ROWS=1000
MAX_RUNNING_JOBS=2
MAX_WAITING_JOBS=3
JOB_RESULT_TTL_SECONDS=900
FAILED_JOB_TTL_SECONDS=60
MAX_JOB_LIFETIME_SECONDS=1800
DNS_TIMEOUT_SECONDS=3
DNS_CONCURRENCY=20
RATE_SINGLE_PER_MIN=20
RATE_BULK_PER_HOUR=5
MEMORY_GUARD_MB=380
```

---

## Final repo layout (what you will have after C7)

```
P:\mail_validator\
├── backend\
│   ├── app\
│   │   ├── api\          ← routes, schemas, middleware
│   │   ├── services\     ← job manager, csv service, rate limiter
│   │   ├── core\         ← validation logic, dns resolver
│   │   └── main.py
│   ├── tests\
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend\
│   ├── src\
│   │   ├── api\
│   │   ├── components\
│   │   └── pages\
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── Dockerfile
├── .github\workflows\ci.yml
├── .env.example
└── README.md
```

---

## Chunk dependency chain

```
C0 (Foundation)
  └─► C1 (Validation core)
        ├─► C2 (Single API + UI)
        │     └─► C4 (Bulk UI) ◄──┐
        └─► C3 (Bulk engine) ──────┘
              └─► C5 (Hardening)
                    └─► C6 (Deploy)
                          └─► C7 (Load test + Release)
```

**Never start a chunk before its parent exits green.**

---

## Commit convention

```
git commit -m "C0: project skeleton and health endpoint"
git commit -m "C1: validation core – syntax, DNS, scoring"
git commit -m "C2: single-check API and React form"
# ...
```

---

## If the model gets stuck or produces wrong code

1. Paste the error message in the chat and ask it to fix it.
2. If it can't fix it in two attempts, switch to Claude Opus 4.6 Thinking for that specific fix.
3. For DNS-related failures, check that your machine can resolve MX records:
   ```powershell
   Resolve-DnsName -Name gmail.com -Type MX
   ```
4. For Docker build failures, run `docker build -t mailcheck . 2>&1 | more` to see the full log.
