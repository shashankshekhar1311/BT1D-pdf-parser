import os
import shutil
import tempfile
from fastapi import FastAPI, File, UploadFile, HTTPException
from extractor import PDFBatchExtractor
from schemas import DocumentExtractionResponse

app = FastAPI(title="PDF Check Extractor API", version="1.0")

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

@app.post("/api/v1/extract-pdf", response_model=DocumentExtractionResponse)
async def extract_pdf(file: UploadFile = File(...)):
    # Safely handle missing filenames from CAI
    print(f"\n[>>> INCOMING REQUEST RECEIVED <<<] Filename: {file.filename}", flush=True)
    safe_filename = file.filename if file.filename else "uploaded_document.pdf"
    
    if not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    temp_dir = tempfile.mkdtemp()
    temp_pdf_path = os.path.join(temp_dir, safe_filename)
    
    try:
        with open(temp_pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"[API] Saved temp file ({os.path.getsize(temp_pdf_path)} bytes). Starting extraction...", flush=True)
        # Verify file received content before running PyMuPDF
        if os.path.getsize(temp_pdf_path) == 0:
            raise HTTPException(status_code=400, detail="Uploaded PDF file is empty or missing content.")
            
        # Run Vision-LLM extraction pipeline
        result = extractor.process_pdf(temp_pdf_path)
        print(f"[API] Extraction completed successfully!", flush=True)
        # Return Pydantic object directly to allow FastAPI to handle Enum & JSON encoding
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Extraction Pipeline Exception: {str(e)}")
        print(f"[API ERROR]: {str(e)}", flush=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)