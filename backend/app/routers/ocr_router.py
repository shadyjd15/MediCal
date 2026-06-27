import io
import re
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from .. import auth, models, schemas

router = APIRouter(prefix="/api/ocr", tags=["ocr"])

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:  # pragma: no cover
    OCR_AVAILABLE = False


DOSE_PATTERN = re.compile(r"\b\d+(\.\d+)?\s?(mg|mcg|g|ml)\b", re.IGNORECASE)
DOCTOR_PATTERN = re.compile(r"(Dr\.?\s+[A-Z][a-zA-Z.\s]{2,40})")
HOSPITAL_PATTERN = re.compile(r"([A-Z][a-zA-Z\s]{2,40}(Hospital|Clinic|Medical Center|Healthcare))")


@router.post("/scan", response_model=schemas.OcrResult)
def scan_prescription(file: UploadFile = File(...), user: models.User = Depends(auth.get_current_user)):
    if not OCR_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="OCR engine is not available on this server. Make sure tesseract-ocr is installed in the backend image.",
        )

    try:
        contents = file.file.read()
        image = Image.open(io.BytesIO(contents))
        raw_text = pytesseract.image_to_string(image)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Could not read image for OCR: {e}")

    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

    dose_match = DOSE_PATTERN.search(raw_text)
    doctor_match = DOCTOR_PATTERN.search(raw_text)
    hospital_match = HOSPITAL_PATTERN.search(raw_text)

    # Best-effort: the first reasonably long line that isn't a doctor/hospital line is
    # often the medicine name on a typed prescription template — purely a starting guess
    # for the user to confirm or edit, never auto-saved without review.
    guessed_name = None
    for line in lines:
        if doctor_match and doctor_match.group(0) in line:
            continue
        if hospital_match and hospital_match.group(0) in line:
            continue
        if len(line) >= 3 and len(line) <= 40 and not line.isdigit():
            guessed_name = line
            break

    return schemas.OcrResult(
        raw_text=raw_text,
        guessed_medicine_name=guessed_name,
        guessed_composition=None,
        guessed_dose=dose_match.group(0) if dose_match else None,
        guessed_doctor_name=doctor_match.group(0) if doctor_match else None,
        guessed_hospital_name=hospital_match.group(0) if hospital_match else None,
    )
