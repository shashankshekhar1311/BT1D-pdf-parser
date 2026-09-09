# PDF Parser Status Snapshot

## Project
- Workspace: D:\pdf_parser
- Current date: 2026-09-09

## Verified runtime state
- 148 model service is the GPU-backed inference service.
- 152 gateway is the API orchestration layer.
- 148 runs on port 9000.
- 152 runs on port 8000.
- Production architecture is: 152 -> 148 internal infer endpoint.

## Verified facts
- Real large PDF inference succeeded on the 148 model service.
- Evidence: status=200, elapsed_seconds=1690.6.
- That corresponds to approximately 28.2 minutes for one large PDF.
- The extraction response included donor notes and relevant grant summary data.
- The page filter is not dropping donor/memo/handwritten signal pages.
- Project tests pass.
- Evidence: `python -m unittest discover -s tests -p "test_*.py" -q` -> `Ran 7 tests in 0.239s`, `OK`.

## Current architecture
- 148/service: internal GPU inference service
- 152/gateway: batch API gateway
- Internal contract: 152 calls 148 /infer with a PDF upload
- Batch response is aggregated in the gateway before returning to the caller

## Important operational constraints
- The model service is heavy and long-running.
- Do not run multiple page-level model jobs in parallel on the same GPU worker.
- Gateway concurrency should stay conservative.
- If port 8000 or 9000 is already in use, kill the stale listener before starting the service.

## Startup commands
### 148 model service
```powershell
cd D:\pdf_parser
.\.venv\Scripts\python.exe 148\scripts\start_model_service_148.py
```

### 152 gateway
```powershell
cd D:\pdf_parser
.\.venv\Scripts\python.exe 152\scripts\start_gateway_152.py
```

## Health checks
### 148
```powershell
Invoke-RestMethod http://127.0.0.1:9000/health
```

### 152
```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Batch call format
```powershell
$files = @(
  @{ name = 'BT1D_010226_B001.pdf'; path = 'D:\pdf_parser\input\BT1D_010226_B001.pdf' },
  @{ name = 'BT1D_010226_C001.pdf'; path = 'D:\pdf_parser\input\BT1D_010226_C001.pdf' }
)

$body = @{}
$body['files'] = @(
  (Get-Item $files[0].path),
  (Get-Item $files[1].path)
)

Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/extract-batch' -Method Post -Form $body
```

## Known issue
- The gateway error path previously returned an empty detail string when the model service failed or was not ready.
- This was fixed by improving error reporting in the gateway.

## Current next step
- Keep the 148 service and 152 gateway running.
- Use this snapshot as the resume point for the next session.
