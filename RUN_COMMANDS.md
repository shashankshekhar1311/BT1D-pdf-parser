# Exact Run Commands

## 148: model service (approved production model)
```bat
cd /d D:\pdf_parser
python 148\scripts\start_model_service_148.py
```

## 148: developer mode (experiments and tuning)
```bat
cd /d D:\pdf_parser
call .venv\Scripts\activate.bat
uvicorn api:app --host 0.0.0.0 --port 8001 --reload
```

## 152: production gateway
```bat
cd /d D:\pdf_parser
python 152\scripts\start_gateway_152.py
```

## Health checks
```http
GET http://127.0.0.1:9000/health
GET http://127.0.0.1:8000/health
```

## Batch extraction example
```http
POST http://127.0.0.1:8000/api/v1/extract-batch
Content-Type: multipart/form-data
```
