from __future__ import annotations

import asyncio
import os
from typing import Any, List

import httpx
from fastapi import FastAPI, HTTPException, UploadFile, File

from schemas import DocumentExtractionResponse

app = FastAPI(title="PDF Gateway Service (152)", version="1.0")

MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://127.0.0.1:9000/infer")
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1_0_0")
MAX_CONCURRENT_PDFS = int(os.getenv("MAX_CONCURRENT_PDFS", "3"))


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "healthy",
        "environment": "152-gateway",
        "model_version": MODEL_VERSION,
        "internal_model_service": MODEL_SERVICE_URL,
        "max_concurrent_pdfs": MAX_CONCURRENT_PDFS,
    }


async def _process_single_pdf(file: UploadFile) -> tuple[DocumentExtractionResponse | None, str | None]:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return None, f"{file.filename or 'unknown'} is not a PDF file."

    try:
        payload = await file.read()
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                MODEL_SERVICE_URL,
                files={"file": (file.filename, payload, "application/pdf")},
            )

        if response.status_code != 200:
            detail = (response.text or "").strip()
            if not detail:
                detail = f"HTTP {response.status_code} from model service with empty response body."
            return None, f"{file.filename}: {detail}"

        return DocumentExtractionResponse.model_validate(response.json()), None
    except Exception as exc:  # pragma: no cover - explicit API error path
        return None, f"{file.filename}: {str(exc)}"


@app.post("/api/v1/extract-batch", response_model=dict)
async def extract_batch(files: List[UploadFile] = File(...)) -> dict[str, Any]:
    if not files:
        raise HTTPException(status_code=400, detail="At least one PDF file is required.")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_PDFS)

    async def guarded_process(file: UploadFile):
        async with semaphore:
            return await _process_single_pdf(file)

    processed = await asyncio.gather(*(guarded_process(file) for file in files))

    results: list[DocumentExtractionResponse] = []
    errors: list[str] = []
    for item, error in processed:
        if error:
            errors.append(error)
        elif item is not None:
            results.append(item)

    if not results and errors:
        raise HTTPException(status_code=500, detail={"errors": errors})

    combined = {
        "filename": "combined_batch_output",
        "total_pages_processed": sum(item.total_pages_processed for item in results),
        "total_batch_count": sum(item.total_batch_count for item in results),
        "total_check_count": sum(item.total_check_count for item in results),
        "grand_total_check_amount": sum(item.grand_total_check_amount for item in results),
        "grand_total_cash_amount": sum(item.grand_total_cash_amount for item in results),
        "results": [item.model_dump() for item in results],
        "errors": errors,
    }
    return combined
