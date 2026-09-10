# Daily Ops Checklist

Use this checklist for routine start, stop, and quick troubleshooting of the 148 model service and 152 gateway.

## 1) Daily startup

### Confirm environment
- Verify the correct runtime is targeted:
  - Dev: 148 on `9001`, gateway on `8001`
  - Prod: 148 on `9000`, gateway on `8000`
- Check that the expected env files are loaded:
  - `148/config/prod_model.env` or `148/config/dev.env`
  - `152/config/prod.env` or `152/config/dev.env`
- Confirm the approved model version is loaded in the registry.

### Start order
1. Start the 148 model service.
2. Wait for health to respond.
3. Start the 152 gateway.
4. Confirm gateway health responds.
5. Run a quick smoke test against the gateway.

### Automated production commands
```powershell
cd D:\pdf_parser
powershell -ExecutionPolicy Bypass -File .\deploy_prod.ps1
```

### Manual server-specific commands
```powershell
cd D:\pdf_parser
powershell -ExecutionPolicy Bypass -File .\148\scripts\setup_148_server.ps1
powershell -ExecutionPolicy Bypass -File .\148\scripts\start_148_server.bat
```

```powershell
cd D:\pdf_parser
powershell -ExecutionPolicy Bypass -File .\152\scripts\setup_152_server.ps1
powershell -ExecutionPolicy Bypass -File .\152\scripts\start_152_server.bat
```

### Safe restart for the 152 production gateway
```powershell
cd D:\pdf_parser
powershell -ExecutionPolicy Bypass -File .\152\scripts\restart_152_prod.ps1
```

### Production examples
```powershell
cd D:\pdf_parser
$env:APP_ENV = 'prod_model'
$env:HOST = '0.0.0.0'
$env:PORT = '9000'
$env:RELOAD = 'false'
$env:MODEL_VERSION = 'v1_0_0'
.
.\.venv\Scripts\python.exe 148\scripts\start_model_service_148.py
```

```powershell
cd D:\pdf_parser
$env:APP_ENV = 'prod'
$env:HOST = '0.0.0.0'
$env:PORT = '8000'
$env:RELOAD = 'false'
$env:MODEL_SERVICE_URL = 'http://127.0.0.1:9000/infer'
.
.\.venv\Scripts\python.exe 152\scripts\start_gateway_152.py
```

### Health checks
```powershell
Invoke-RestMethod http://127.0.0.1:9000/health
Invoke-RestMethod http://127.0.0.1:8000/health
```

For dev, swap ports to 9001 and 8001.

## 2) Daily shutdown

1. Stop the 152 gateway first.
2. Stop the 148 model service second.
3. Confirm no stale listeners remain on the ports.
4. Close the terminal session(s) if they are left open.

```powershell
Get-NetTCPConnection -LocalPort 8000,9000 -ErrorAction SilentlyContinue
Get-NetTCPConnection -LocalPort 8001,9001 -ErrorAction SilentlyContinue
```

## 3) Quick troubleshooting

### Gateway fails to start
- Check the `MODEL_SERVICE_URL` in `152/config/*.env`.
- Ensure the 148 model service is already healthy on the expected port.
- Confirm `PORT` is not already in use.

### Model service fails to start
- Verify the `MODEL_VERSION` and registry path exist.
- Check that the GPU/runtime is available.
- Confirm the environment value matches the intended runtime (`prod_model` or `dev`).

### Port already in use
```powershell
Get-NetTCPConnection -LocalPort 8000,9001,9000,9001 -ErrorAction SilentlyContinue
```
Then stop the stale process before restarting.

For the production gateway, the recommended safe restart is:
```powershell
cd D:\pdf_parser
powershell -ExecutionPolicy Bypass -File .\152\scripts\restart_152_prod.ps1
```

### Health check returns error
- Confirm both services are running.
- Check the terminal output for a Python import/config error.
- Verify the model service is listening before starting the gateway.
- Restart in the order: 148 first, then 152.

## 4) Operational guardrails
- Do not run multiple heavy jobs in parallel on the same GPU worker.
- Keep dev and prod isolated to different ports.
- Do not skip the health check after startup.
- Treat the 152 gateway as the public entry point and the 148 model service as internal.
- If something fails after a config change, restart the model service first and then the gateway.
