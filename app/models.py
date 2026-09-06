import uuid
from datetime import datetime
from sqlalchemy import Column, String, Date, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

def gen_uuid():
    return str(uuid.uuid4())

class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String, primary_key=True, default=gen_uuid)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    sex = Column(String(20), nullable=False)
    phone_number = Column(String(10), nullable=False, index=True)
    email = Column(String(120), nullable=True)
    address_line_1 = Column(String(200), nullable=False)
    address_line_2 = Column(String(200), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(2), nullable=False)
    zip_code = Column(String(10), nullable=False)
    insurance_provider = Column(String(120), nullable=True)
    insurance_member_id = Column(String(50), nullable=True)
    preferred_language = Column(String(50), nullable=False, default="English")
    emergency_contact_name = Column(String(120), nullable=True)
    emergency_contact_phone = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # soft delete ke liye

# --- DB connection setup ---
import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////data/patients.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()