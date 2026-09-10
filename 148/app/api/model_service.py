from __future__ import annotations

import os
import tempfile
from typing import Any

from fastapi import FastAPI, HTTPException, UploadFile, File

from extractor import PDFBatchExtractor
from schemas import DocumentExtractionResponse

app = FastAPI(title="PDF Model Service (148)", version="1.0")

extractor: PDFBatchExtractor | None = None
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1_0_0")


@app.on_event("startup")
def startup_event() -> None:
    global extractor
    print(f"[148-MODEL-SERVICE] Initializing vision model on GPU for version {MODEL_VERSION}...")
    extractor = PDFBatchExtractor()
    print(f"[148-MODEL-SERVICE] Ready for inference requests using version {MODEL_VERSION}.")


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "healthy",
        "environment": "148-model-service",
        "gpu_loaded": extractor is not None,
        "model_version": MODEL_VERSION,
    }


@app.post("/infer", response_model=DocumentExtractionResponse)
async def infer(file: UploadFile = File(...)) -> DocumentExtractionResponse:
    if extractor is None:
        raise HTTPException(status_code=503, detail="Model service not initialized.")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_pdf_path = os.path.join(temp_dir, file.filename)
        with open(temp_pdf_path, "wb") as buffer:
            buffer.write(await file.read())

        try:
            result = extractor.process_pdf(temp_pdf_path)
            return result
        except Exception as exc:  # pragma: no cover - explicit API error path
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(exc)}") from exc
