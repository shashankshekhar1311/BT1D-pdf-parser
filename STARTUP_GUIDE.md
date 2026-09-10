# Startup Guide

This project uses a two-service startup model:

- 148 is the GPU-backed model service
- 152 is the gateway that calls the model service and exposes the batch API

The service topology is:

```text
152 gateway -> 148 model service /infer
```

## Environment layout

### Development
- Model service: `http://127.0.0.1:9001`
- Gateway: `http://127.0.0.1:8001`
- Purpose: local iteration without disrupting production traffic

### Production
- Model service: `http://127.0.0.1:9000`
- Gateway: `http://127.0.0.1:8000`
- Purpose: normal runtime path used for real extraction work

### Environment file conventions
The project keeps separate runtime configuration files for each environment so the dev and prod services can run side by side on different ports. The production gateway config follows the same pattern shown in the app's env file:

```dotenv
APP_ENV=prod
HOST=0.0.0.0
PORT=8000
RELOAD=false
MODEL_SERVICE_URL=http://127.0.0.1:9000/infer
MODEL_VERSION=v1_0_0
INPUT_MODE=batch
OUTPUT_MODE=combined_json
PYTHONPATH=D:\pdf_parser
INTERNAL_MODEL_HOST=127.0.0.1
INTERNAL_MODEL_PORT=9000
INTERNAL_MODEL_ENDPOINT=/infer

# Dev companion config uses separate ports so production and development services can run simultaneously.
# For example: dev gateway -> 127.0.0.1:8001 and dev model -> 127.0.0.1:9001.
```

This pattern is mirrored in the dev configuration, but with the dev ports (`8001` and `9001`) and the corresponding model URL pointing to the development service.

## Start the services

### Production deployment pattern for two separate servers
This project is designed to run as two separate services on two separate machines or server processes:

- 148 server: GPU-backed model service
- 152 server: public gateway that forwards inference to the model service

Use the dedicated start scripts below instead of the single-machine batch files when deploying in a split-server layout.

#### 148 model server setup
```powershell
cd D:\pdf_parser
powershell -ExecutionPolicy Bypass -File .\148\scripts\setup_148_server.ps1
& ".\148\scripts\start_148_server.bat"
```

#### 152 gateway server setup
```powershell
cd D:\pdf_parser
powershell -ExecutionPolicy Bypass -File .\152\scripts\setup_152_server.ps1
& ".\152\scripts\start_152_server.bat"
```

> Important: the 152 launch script now checks for a stale listener on the default gateway port before starting. If port `8000` is already occupied by an old instance, it stops that process automatically to avoid the `Errno 10048` bind failure.
>
> Always run the batch file from the repo root (`D:\pdf_parser`) so the relative paths resolve correctly.

### Option A: use the repo batch scripts

#### Development model service
```powershell
cd D:\pdf_parser
& ".\148\scripts\start_dev_148.bat"
```

#### Development gateway
```powershell
cd D:\pdf_parser
& ".\152\scripts\start_dev_152.bat"
```

#### Production model service
```powershell
cd D:\pdf_parser
& ".\148\scripts\start_prod_model_148.bat"
```

#### Production gateway
```powershell
cd D:\pdf_parser
& ".\152\scripts\start_152_gateway.bat"
```

### Option B: start the Python entrypoints directly

#### Development model service
```powershell
cd D:\pdf_parser
$env:APP_ENV = 'dev'
$env:HOST = '0.0.0.0'
$env:PORT = '9001'
$env:RELOAD = 'true'
$env:MODEL_VERSION = 'v1_0_0'
$env:MODEL_PATH = 'D:/pdf_parser/148/registry/models/qwen2_5_vl/v1_0_0'
.\.venv\Scripts\python.exe 148\scripts\start_model_service_148.py
```

#### Development gateway
```powershell
cd D:\pdf_parser
$env:APP_ENV = 'dev'
$env:HOST = '0.0.0.0'
$env:PORT = '8001'
$env:RELOAD = 'true'
$env:MODEL_VERSION = 'v1_0_0'
$env:MODEL_SERVICE_URL = 'http://127.0.0.1:9001/infer'
$env:MODEL_PATH = 'D:/pdf_parser/148/registry/models/qwen2_5_vl/v1_0_0'
.\.venv\Scripts\python.exe 152\scripts\start_gateway_152.py
```

#### Production model service
```powershell
cd D:\pdf_parser
$env:APP_ENV = 'prod_model'
$env:HOST = '0.0.0.0'
$env:PORT = '9000'
$env:RELOAD = 'false'
$env:MODEL_VERSION = 'v1_0_0'
.\.venv\Scripts\python.exe 148\scripts\start_model_service_148.py
```

#### Production gateway
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

### 148 model service
```powershell
Invoke-RestMethod http://127.0.0.1:9000/health
```

### 152 gateway
```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

For development, swap the port numbers to 9001 and 8001.

## One-shot local dev deployment
For local development on the same machine, use the dev deployment flow so the separate port pairs remain clean and isolated:

```powershell
cd D:\pdf_parser
powershell -ExecutionPolicy Bypass -File .\deploy_dev.ps1
```

This script does the following:

1. pulls the latest GitHub `main` code
2. seeds the 148 local dev environment
3. seeds the 152 local dev environment
4. clears stale listeners on ports 8001 and 9001
5. starts the dev model service on 9001
6. waits for the model to initialize
7. starts the dev gateway on 8001
8. validates both local dev health endpoints

## One-shot production deployment
Use the repo-level deployment script for a safe prod restart:

```powershell
cd D:\pdf_parser
powershell -ExecutionPolicy Bypass -File .\deploy_prod.ps1
```

This script does the following:

1. pulls the latest GitHub `main` code
2. validates and sets up the 148 model server environment
3. validates and sets up the 152 gateway environment
4. clears stale listeners on ports 8000 and 9000
5. starts the model service first
6. waits for the model to initialize
7. starts the gateway second
8. verifies both health endpoints return `200 OK`

## Startup order

1. Start the 148 model service.
2. Confirm the service health endpoint responds.
3. Start the 152 gateway.
4. Confirm the gateway health endpoint responds.
5. Submit a batch extraction request to the gateway.

## Operational guidance

- Do not run multiple heavy inference jobs in parallel on the same GPU worker.
- Development and production can run at the same time because they are isolated to different ports.
- If a port is already in use, stop the stale listener before restarting.
- The gateway is the only public entry point; the model service is internal and should not be called directly by end users.
- When running on separate machines, the gateway must point to the model server's correct `MODEL_SERVICE_URL` value and not assume the model is local.
- For production restarts, always stop stale listeners on `8000`/`9000` before starting new services.

## Notes

- The .ps1 files are for environment setup and bootstrap tasks.
- The .bat files are the runtime launchers that actually start the model service and gateway.
- The correct way to invoke a .bat launcher from PowerShell is `& ".\path\to\script.bat"`.
- The older generic `start_gpu.bat` guidance is not the active project startup path.
- The current startup path is the two-service model described above using the scripts in the `148\scripts` and `152\scripts` folders.
