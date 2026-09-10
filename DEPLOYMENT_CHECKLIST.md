# Production Deployment Checklist

This checklist is for keeping the approved model version on 148 and the production gateway on 152 separated and stable.

## 1. Confirm the approved model version
- Confirm the approved model version in [148/registry/models/qwen2_5_vl/production/current_version.txt](148/registry/models/qwen2_5_vl/production/current_version.txt)
- Verify metadata exists in [148/registry/models/qwen2_5_vl/v1_0_0/metadata.json](148/registry/models/qwen2_5_vl/v1_0_0/metadata.json)
- Verify validation report exists in [148/registry/models/qwen2_5_vl/v1_0_0/validation_report.json](148/registry/models/qwen2_5_vl/v1_0_0/validation_report.json)

## 2. Confirm 148 model service config
- Ensure [148/config/prod_model.env](148/config/prod_model.env) contains the approved `MODEL_VERSION`
- Verify `MODEL_PATH` points to the approved registry folder
- Verify `HOST`, `PORT`, and `RELOAD=false`
- Ensure the service owns the GPU model runtime

## 3. Confirm 152 gateway config
- Ensure [152/config/prod.env](152/config/prod.env) contains the correct `MODEL_SERVICE_URL`
- Ensure `MODEL_VERSION` matches the approved version
- Verify `PORT=8000`
- Verify `RELOAD=false`

## 4. Start the model service on 148
Run:
```bat
cd /d D:\pdf_parser
python 148\scripts\start_model_service_148.py
```

Validate:
```http
GET http://127.0.0.1:9000/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "148-model-service",
  "gpu_loaded": true,
  "model_version": "v1_0_0"
}
```

## 5. Start the gateway on 152
Run:
```bat
cd /d D:\pdf_parser
python 152\scripts\start_gateway_152.py
```

Validate:
```http
GET http://127.0.0.1:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "152-gateway",
  "model_version": "v1_0_0",
  "internal_model_service": "http://127.0.0.1:9000/infer"
}
```

## 6. Validate a batch extraction request
Use the request payload below against the 152 gateway.

## 7. Rollback procedure
- If the approved version fails, update the registry pointer to the previous approved version
- Update the config for the 148 model service to the prior version
- Restart the 148 model service
- Restart the 152 gateway
- Re-run the health checks

## 8. Operational guardrails
- Never run the dev app and production model service in the same process
- Never use reload on the production runtime
- Do not edit the production model service directly during active traffic
- Keep all model changes in the 148 registry before promoting to 152
