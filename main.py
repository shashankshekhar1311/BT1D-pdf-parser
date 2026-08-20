from fastapi import FastAPI, UploadFile, File, HTTPException
import tempfile
import os
from schemas import DocumentExtractionResponse
from extractor import PDFBatchExtractor
app = FastAPI(
   title="PDF Check & Batch Extraction Service",
   version="1.0",
   description="GPU/CPU-Accelerated PDF Parser for Informatica IDMC"
)
extractor = PDFBatchExtractor()

@app.get("/health")
def health_check():
   return {"status": "healthy", "service": "PDF Batch Extractor"}

@app.post("/extract-pdf", response_model=DocumentExtractionResponse)
async def extract_pdf_endpoint(file: UploadFile = File(...)):
   if not file.filename.lower().endswith(".pdf"):
       raise HTTPException(status_code=400, detail="Only PDF files are supported.")
   with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
       content = await file.read()
       tmp.write(content)
       tmp_path = tmp.name
   try:
       extraction_result = extractor.process_pdf(tmp_path)
       extraction_result.filename = file.filename
       return extraction_result
   finally:
       if os.path.exists(tmp_path):
           os.remove(tmp_path)