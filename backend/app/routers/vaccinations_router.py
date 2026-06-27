import os
import shutil
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/vaccinations", tags=["vaccinations"])

UPLOAD_DIR = "uploads/vaccinations"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _scope_query(db: Session, user: models.User):
    q = db.query(models.Vaccination)
    if user.role != models.RoleEnum.admin:
        q = q.filter(models.Vaccination.user_id == user.id)
    return q


@router.get("", response_model=List[schemas.VaccinationOut])
def list_vaccinations(db: Session = Depends(get_db), user: models.User = Depends(auth.get_current_user)):
    return _scope_query(db, user).order_by(models.Vaccination.date_administered.desc()).all()


@router.post("", response_model=schemas.VaccinationOut)
def create_vaccination(payload: schemas.VaccinationCreate, db: Session = Depends(get_db), user: models.User = Depends(auth.get_current_user)):
    v = models.Vaccination(user_id=user.id, **payload.model_dump())
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@router.put("/{vac_id}", response_model=schemas.VaccinationOut)
def update_vaccination(vac_id: str, payload: schemas.VaccinationUpdate, db: Session = Depends(get_db), user: models.User = Depends(auth.get_current_user)):
    v = _scope_query(db, user).filter(models.Vaccination.id == vac_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vaccination record not found")
    for k, val in payload.model_dump(exclude_unset=True).items():
        setattr(v, k, val)
    db.commit()
    db.refresh(v)
    return v


@router.post("/{vac_id}/certificate", response_model=schemas.VaccinationOut)
def upload_certificate(vac_id: str, certificate: UploadFile = File(...), db: Session = Depends(get_db), user: models.User = Depends(auth.get_current_user)):
    v = _scope_query(db, user).filter(models.Vaccination.id == vac_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vaccination record not found")
    ext = os.path.splitext(certificate.filename)[1]
    fname = f"{uuid.uuid4()}{ext}"
    full_path = os.path.join(UPLOAD_DIR, fname)
    with open(full_path, "wb") as f:
        shutil.copyfileobj(certificate.file, f)
    v.certificate_file = f"/uploads/vaccinations/{fname}"
    db.commit()
    db.refresh(v)
    return v


@router.delete("/{vac_id}")
def delete_vaccination(vac_id: str, db: Session = Depends(get_db), user: models.User = Depends(auth.get_current_user)):
    v = _scope_query(db, user).filter(models.Vaccination.id == vac_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vaccination record not found")
    db.delete(v)
    db.commit()
    return {"ok": True}
