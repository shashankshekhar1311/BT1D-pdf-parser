import os
import shutil
import tempfile
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from pydantic import BaseModel
from extractor import PDFBatchExtractor
app = FastAPI(title="PDF Check Extractor API", version="1.0")
# Global model instance loaded ONCE into GPU memory at server startup
extractor = None
@app.on_event("startup")
def load_vision_model():
    global extractor
    print("Initializing Vision-LLM model on GPU...")
    extractor = PDFBatchExtractor()
    print("Model ready for API requests.")
@app.get("/health")
def health_check():
    return {"status": "healthy", "gpu_loaded": extractor is not None}
@app.post("/api/v1/extract-pdf")
async def extract_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    # Save uploaded PDF to temporary file
    temp_dir = tempfile.mkdtemp()
    temp_pdf_path = os.path.join(temp_dir, file.filename)
    try:
        with open(temp_pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        # Run Vision-LLM extraction pipeline
        result = extractor.process_pdf(temp_pdf_path)
        return result.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary storage
        shutil.rmtree(temp_dir, ignore_errors=True)