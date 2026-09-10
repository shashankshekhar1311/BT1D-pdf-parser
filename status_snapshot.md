# PDF Parser Status Snapshot

## Project
- Workspace: D:\pdf_parser
- Current date: 2026-09-09

## Verified runtime architecture
- 148 is the GPU-backed model service.
- 152 is the gateway API layer.
- Production model service runs on port 9000.
- Production gateway runs on port 8000.
- Development model service runs on port 9001.
- Development gateway runs on port 8001.
- Internal contract: gateway calls the model service at `http://127.0.0.1:<port>/infer`.

## Verified facts
- Real large PDF inference succeeded on the 148 model service.
- Evidence: status=200, elapsed_seconds=1690.6.
- That corresponds to approximately 28.2 minutes for one large PDF.
- The extraction response included donor notes and grant summary content.
- Page filtering is preserving memo/donor/handwritten signal pages.
- Automated tests remain passing.
- Evidence: `python -m unittest discover -s tests -p "test_*.py" -q` -> `Ran 7 tests in 0.239s`, `OK`.

## Active startup matrix

### Development
- Model: 148 service on 9001, `APP_ENV=dev`, `RELOAD=true`
- Gateway: 152 on 8001, `APP_ENV=dev`, `RELOAD=true`
- Purpose: local development and test iteration without touching production ports

### Production
- Model: 148 service on 9000, `APP_ENV=prod_model`, `RELOAD=false`
- Gateway: 152 on 8000, `APP_ENV=prod`, `RELOAD=false`
- Purpose: deployed runtime path for normal batch extraction work

## Startup commands

### Start development model service
```powershell
cd D:\pdf_parser
148\scripts\start_dev_148.bat
```

### Start development gateway
```powershell
cd D:\pdf_parser
152\scripts\start_dev_152.bat
```

### Start production model service
```powershell
cd D:\pdf_parser
148\scripts\start_prod_model_148.bat
```

### Start production gateway
```powershell
cd D:\pdf_parser
152\scripts\start_152_gateway.bat
```

## Direct Python startup (manual env setup)

### 148 dev
```powershell
cd D:\pdf_parser
$env:APP_ENV = 'dev'
$env:HOST = '0.0.0.0'
$env:PORT = '9001'
$env:RELOAD = 'true'
$env:MODEL_VERSION = 'dev'
.\.venv\Scripts\python.exe 148\scripts\start_model_service_148.py
```

### 152 dev
```powershell
cd D:\pdf_parser
$env:APP_ENV = 'dev'
$env:HOST = '0.0.0.0'
$env:PORT = '8001'
$env:RELOAD = 'true'
$env:MODEL_SERVICE_URL = 'http://127.0.0.1:9001/infer'
.\.venv\Scripts\python.exe 152\scripts\start_gateway_152.py
```

### 148 prod
```powershell
cd D:\pdf_parser
$env:APP_ENV = 'prod_model'
$env:HOST = '0.0.0.0'
$env:PORT = '9000'
$env:RELOAD = 'false'
$env:MODEL_VERSION = 'v1_0_0'
.\.venv\Scripts\python.exe 148\scripts\start_model_service_148.py
```

### 152 prod
```powershell
cd D:\pdf_parser
$env:APP_ENV = 'prod'
$env:HOST = '0.0.0.0'
$env:PORT = '8000'
$env:RELOAD = 'false'
$env:MODEL_SERVICE_URL = 'http://127.0.0.1:9000/infer'
.\.venv\Scripts\python.exe 152\scripts\start_gateway_152.py
```

## Health checks

### Development model service
```powershell
Invoke-RestMethod http://127.0.0.1:9001/health
```

### Development gateway
```powershell
Invoke-RestMethod http://127.0.0.1:8001/health
```

### Production model service
```powershell
Invoke-RestMethod http://127.0.0.1:9000/health
```

### Production gateway
```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Operational notes
- The model service is heavy and long-running; avoid running multiple page-level inference jobs in parallel on the same GPU worker.
- Development and production can run side-by-side because they use different ports.
- If a port is already occupied, stop the stale listener before restarting the service.
- The gateway depends on the model service being healthy before batch extraction requests are sent.

## Current next step
- Keep the prod services stable for normal work.
- Use dev ports 9001/8001 for iteration and debugging without affecting prod.
