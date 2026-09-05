import re
from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict

VALID_SEX = {"Male", "Female", "Other", "Decline to Answer"}
US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC"
}

class PatientBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    sex: str
    phone_number: str
    email: Optional[EmailStr] = None
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = "English"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v):
        if not (1 <= len(v) <= 50):
            raise ValueError("must be 1-50 characters")
        if not re.match(r"^[A-Za-z'\-\s]+$", v):
            raise ValueError("must be alphabetic (hyphens/apostrophes allowed)")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v):
        if v > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return v

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, v):
        if v not in VALID_SEX:
            raise ValueError(f"must be one of {VALID_SEX}")
        return v

    @field_validator("phone_number", "emergency_contact_phone")
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        digits = re.sub(r"\D", "", v)
        if len(digits) != 10:
            raise ValueError("must be a valid 10-digit US phone number")
        return digits

    @field_validator("state")
    @classmethod
    def validate_state(cls, v):
        v = v.upper()
        if v not in US_STATES:
            raise ValueError("must be a valid 2-letter US state abbreviation")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v):
        if not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("must be 5-digit or ZIP+4 US format")
        return v

    @field_validator("city")
    @classmethod
    def validate_city(cls, v):
        if not (1 <= len(v) <= 100):
            raise ValueError("must be 1-100 characters")
        return v

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    sex: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    model_config = ConfigDict(extra="ignore")