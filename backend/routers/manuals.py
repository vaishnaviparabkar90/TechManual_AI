
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.core.config import UPLOAD_DIR
from backend.schemas import UploadResponse
from backend.services.ingestion import ingest_pdf

router = APIRouter(prefix="/manuals", tags=["Manuals"])


@router.post("/upload", response_model=UploadResponse)
def upload_manual(file: UploadFile = File(...)):
    """Upload a PDF manual and store its chunks in ChromaDB."""

    if not file.filename or Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed.",
        )

    # Create a unique filename to avoid overwriting another upload.
    safe_filename = f"{uuid4().hex}_{Path(file.filename).name}"
    file_path = UPLOAD_DIR / safe_filename

    try:
        with file_path.open("wb") as destination:
            while content := file.file.read(1024 * 1024):
                destination.write(content)

        result = ingest_pdf(file_path)

        return UploadResponse(**result)

    except ValueError as error:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(error)) from error

    except Exception as error:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to process the uploaded manual.",
        ) from error

    finally:
        file.file.close()
