import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models import Patient, init_db, get_db
from app.schemas import PatientCreate, PatientUpdate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("patient-api")

app = FastAPI(title="Patient Registration API", version="1.0.0")


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("Database initialized.")


def envelope(data=None, error=None):
    return {"data": data, "error": error}



@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = jsonable_encoder(exc.errors(), exclude={"ctx"})
    return JSONResponse(status_code=422, content=envelope(error=errors))


@app.exception_handler(ValidationError)
async def pydantic_validation_handler(request, exc):
    errors = jsonable_encoder(exc.errors(), exclude={"ctx"})
    return JSONResponse(status_code=422, content=envelope(error=errors))


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content=envelope(error=exc.detail))


def serialize(p: Patient) -> dict:
    return {
        "patient_id": p.patient_id,
        "first_name": p.first_name,
        "last_name": p.last_name,
        "date_of_birth": p.date_of_birth.isoformat(),
        "sex": p.sex,
        "phone_number": p.phone_number,
        "email": p.email,
        "address_line_1": p.address_line_1,
        "address_line_2": p.address_line_2,
        "city": p.city,
        "state": p.state,
        "zip_code": p.zip_code,
        "insurance_provider": p.insurance_provider,
        "insurance_member_id": p.insurance_member_id,
        "preferred_language": p.preferred_language,
        "emergency_contact_name": p.emergency_contact_name,
        "emergency_contact_phone": p.emergency_contact_phone,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


@app.get("/health")
def health():
    return envelope(data={"status": "ok"})


@app.get("/patients")
def list_patients(
    last_name: Optional[str] = Query(None),
    date_of_birth: Optional[str] = Query(None),
    phone_number: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Patient).filter(Patient.deleted_at.is_(None))
    if last_name:
        q = q.filter(Patient.last_name.ilike(last_name))
    if date_of_birth:
        q = q.filter(Patient.date_of_birth == date_of_birth)
    if phone_number:
        digits = "".join(ch for ch in phone_number if ch.isdigit())
        q = q.filter(Patient.phone_number == digits)
    results = q.all()
    return envelope(data=[serialize(p) for p in results])


@app.get("/patients/lookup")
def lookup_by_phone(phone_number: str, db: Session = Depends(get_db)):
    """Bonus: voice agent isay call karega returning caller check karne ke liye"""
    digits = "".join(ch for ch in phone_number if ch.isdigit())
    patient = (
        db.query(Patient)
        .filter(Patient.phone_number == digits, Patient.deleted_at.is_(None))
        .first()
    )
    if not patient:
        return envelope(data=None)
    return envelope(data=serialize(patient))


@app.get("/patients/{patient_id}")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = (
        db.query(Patient)
        .filter(Patient.patient_id == patient_id, Patient.deleted_at.is_(None))
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return envelope(data=serialize(patient))


@app.post("/patients", status_code=201)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    try:
        patient = Patient(**payload.model_dump())
        db.add(patient)
        db.commit()
        db.refresh(patient)
    except Exception as e:
        db.rollback()
        logger.error(f"DB write failed on create_patient: {e}")
        raise HTTPException(status_code=500, detail="Failed to save patient record")

    logger.info(f"Created patient {patient.patient_id}: {serialize(patient)}")
    return envelope(data=serialize(patient))


@app.put("/patients/{patient_id}")
def update_patient(patient_id: str, payload: PatientUpdate, db: Session = Depends(get_db)):
    patient = (
        db.query(Patient)
        .filter(Patient.patient_id == patient_id, Patient.deleted_at.is_(None))
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)

    try:
        db.commit()
        db.refresh(patient)
    except Exception as e:
        db.rollback()
        logger.error(f"DB write failed on update_patient: {e}")
        raise HTTPException(status_code=500, detail="Failed to update patient record")

    logger.info(f"Updated patient {patient.patient_id}: {serialize(patient)}")
    return envelope(data=serialize(patient))


@app.delete("/patients/{patient_id}")
def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = (
        db.query(Patient)
        .filter(Patient.patient_id == patient_id, Patient.deleted_at.is_(None))
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient.deleted_at = datetime.utcnow()
    db.commit()
    logger.info(f"Soft-deleted patient {patient_id}")
    return envelope(data={"patient_id": patient_id, "deleted": True})