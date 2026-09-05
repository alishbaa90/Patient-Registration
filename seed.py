"""Optional: seed 2 demo patients so the API isn't empty on first run."""
from datetime import date
from app.models import init_db, SessionLocal, Patient

init_db()
db = SessionLocal()

if db.query(Patient).count() == 0:
    db.add_all([
        Patient(
            first_name="Jane", last_name="Doe", date_of_birth=date(1990, 5, 12),
            sex="Female", phone_number="5551234567", email="jane.doe@example.com",
            address_line_1="123 Main St", city="Austin", state="TX", zip_code="73301",
            preferred_language="English",
        ),
        Patient(
            first_name="John", last_name="Smith", date_of_birth=date(1985, 11, 3),
            sex="Male", phone_number="5559876543", email="john.smith@example.com",
            address_line_1="456 Oak Ave", city="Dallas", state="TX", zip_code="75201",
            preferred_language="English",
        ),
    ])
    db.commit()
    print("Seeded 2 demo patients.")
else:
    print("Patients already exist, skipping seed.")

db.close()