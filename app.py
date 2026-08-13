import os
import shutil
import uuid
import json
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.redactor import PIIRedactor
from src.faker_provider import FakeDataGenerator

app = FastAPI(
    title="PII Redaction API",
    description="API for detecting, redacting, and reporting PII in Word documents",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent

if os.environ.get("VERCEL"):
    STORAGE_DIR = Path("/tmp") / "web_sessions"
else:
    STORAGE_DIR = BASE_DIR / "output" / "web_sessions"

STORAGE_DIR.mkdir(parents=True, exist_ok=True)




@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "PII Redaction Engine is operational"}


@app.post("/api/redact")
async def redact_document(
    file: UploadFile = File(...),
    confidence: float = Form(0.65),
    reset_cache: bool = Form(False)
):
    """
    Accepts a .docx file upload, executes PII detection & redaction,
    and returns metrics, mapping details, text preview, and download links.
    """
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported.")

    if not (0.0 <= confidence <= 1.0):
        raise HTTPException(status_code=400, detail="Confidence threshold must be between 0.0 and 1.0.")

    session_id = uuid.uuid4().hex
    session_dir = STORAGE_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)



    input_path = session_dir / "original_input.docx"
    redacted_path = session_dir / "redacted_document.docx"
    original_copy_path = session_dir / "original_document.docx"
    mapping_path = session_dir / "pii_mapping.json"
    report_path = session_dir / "evaluation_report.md"

    start_time = time.time()

    # Save uploaded file
    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    original_size = input_path.stat().st_size

    # Reset fake data cache if requested
    if reset_cache:
        FakeDataGenerator.reset_cache()

    try:
        redactor = PIIRedactor(str(input_path))

        # Capture original text before redaction
        original_text = redactor.docx_handler.extract_text_with_positions()

        # Run redaction pipeline
        num_replacements, stats = redactor.redact(min_confidence=confidence)

        # Capture redacted text after redaction
        redacted_text = redactor.docx_handler.extract_text_with_positions()

        # Save all output artifacts
        redactor.save_redacted(str(redacted_path))
        redactor.save_original_copy(str(original_copy_path))
        redactor.save_mapping(str(mapping_path))
        redactor.generate_evaluation_report(str(report_path), stats)

        process_duration = round(time.time() - start_time, 3)

        return JSONResponse({
            "success": True,
            "session_id": session_id,
            "file_info": {
                "filename": file.filename,
                "size_bytes": original_size,
                "confidence_threshold": confidence,
                "processing_time_seconds": process_duration
            },
            "stats": stats,
            "mapping": redactor.mapping,
            "original_text": original_text,
            "redacted_text": redacted_text,
            "num_replacements": num_replacements,
            "downloads": {
                "redacted": f"/api/download/{session_id}/redacted",
                "original": f"/api/download/{session_id}/original",
                "mapping": f"/api/download/{session_id}/mapping",
                "report": f"/api/download/{session_id}/report"
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redaction process error: {str(e)}")


@app.get("/api/download/{session_id}/{file_type}")
def download_file(session_id: str, file_type: str):
    session_dir = STORAGE_DIR / session_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found.")

    file_map = {
        "redacted": (session_dir / "redacted_document.docx", "redacted_document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        "original": (session_dir / "original_document.docx", "original_document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        "mapping": (session_dir / "pii_mapping.json", "pii_mapping.json", "application/json"),
        "report": (session_dir / "evaluation_report.md", "evaluation_report.md", "text/markdown"),
    }

    if file_type not in file_map:
        raise HTTPException(status_code=400, detail="Invalid file type requested.")

    file_path, filename, media_type = file_map[file_type]

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested file does not exist.")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )


# Mount static directory for frontend
static_dir = BASE_DIR / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

