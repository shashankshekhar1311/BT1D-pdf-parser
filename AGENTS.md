# AGENTS.md — PDF Parser workspace context

Use this file (and `.cursor/rules/`) to retain architecture context across machines and Cursor sessions.

## What this project is

GPU/CPU-accelerated **PDF check & batch extraction** service consumed by **Informatica IDMC**.

Production is a **two-machine** deployment:

1. **148** (`10.0.0.148`) — GPU-backed **model service**. Loads the vision model (Qwen2.5-VL registry under `148/registry/models/`). Exposes internal inference at `/infer` (prod port **9000**).
2. **152** (`10.0.0.152`) — **API gateway**. Accepts batch PDF uploads from Informatica/SharePoint, forwards each file to 148, aggregates results. Public entry at `/api/v1/extract-batch` (prod port **8000**).

```text
Informatica / SharePoint  →  152 gateway  →  148 /infer
```

Clients must talk to **152 only**. Do not expose or call 148 as a public API.

## Code map

| Area | Location |
|------|----------|
| Model FastAPI app | `148/app/api/model_service.py` |
| Gateway FastAPI app | `152/app/api/gateway.py` |
| Extraction engine | `extractor.py`, `schemas.py` |
| Legacy monolith entry | `main.py` (older single-process path; not the split prod topology) |
| Prod gateway config | `152/config/prod.env` |
| Startup source of truth | `STARTUP_GUIDE.md` |

## Environments

- **Production:** model `http://10.0.0.148:9000`, gateway `http://10.0.0.152:8000`, `MODEL_SERVICE_URL=http://10.0.0.148:9000/infer`
- **Development:** model `:9001`, gateway `:8001`, local URLs — can run beside prod

## Agent working rules

- Prefer PowerShell scripts under `148/scripts` and `152/scripts` (`.ps1` over `.bat`).
- Start **148 before 152**; verify `/health` on both.
- When changing gateway config on 152, ensure `MODEL_SERVICE_URL` still targets the live 148 host.
- Avoid parallel heavy inference on the same GPU worker.
- Read `STARTUP_GUIDE.md` before changing deploy/startup behavior.
