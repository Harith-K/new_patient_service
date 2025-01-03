from fastapi import FastAPI, HTTPException ,Depends, Form, Request
from pydantic import BaseModel ,validator
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Date, Text, JSON, TIMESTAMP
from sqlalchemy.orm import sessionmaker ,Session,relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime
import os
from dotenv import load_dotenv
import logging
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Configure Jinja2 templates directory
templates = Jinja2Templates(directory="templates")  


logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

app = FastAPI()

# Load environment variables from the .env file
load_dotenv()

# Fetch the database configuration from environment variables
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
#adding comment

# Ensure DB_PORT is valid and is an integer
try:
    DB_PORT = int(DB_PORT)  # Convert to integer
except (TypeError, ValueError) as e:
    raise ValueError("DB_PORT is not set correctly. Please ensure it is a valid integer.") from e


# Database setup
#SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:root@localhost:3306/meditrack"
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Pydantic models
class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    gender: str
    date_of_birth: str
    contact_number: str
    email: str
    address: str
    medical_history: dict
    prescriptions: dict
    lab_results: dict

class PatientOut(PatientCreate):
    patient_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True


    @validator("date_of_birth", pre=True)
    def format_date_of_birth(cls, v):
        # Ensure the date is in string format (ISO 8601)
        if isinstance(v, datetime.date):
            return v.isoformat()
        return v

# SQLAlchemy models
class Patient(Base):
    __tablename__ = "healthsyc_patients"
    patient_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(255), index=True)
    last_name = Column(String(255))
    gender = Column(String(255))
    date_of_birth = Column(Date)
    contact_number = Column(String(255))
    email = Column(String(255))
    address = Column(Text)
    medical_history = Column(JSON)
    prescriptions = Column(JSON)
    lab_results = Column(JSON)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


# Create tables
Base.metadata.create_all(bind=engine)


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# API Endpoints
@app.post("/patients/add", response_class=HTMLResponse)
def add_patient(
    first_name: str = Form(...),
    last_name: str = Form(...),
    gender: str = Form(...),
    date_of_birth: str = Form(...),
    contact_number: str = Form(...),
    email: str = Form(...),
    address: str = Form(...),
    db: Session = Depends(get_db),
):
    new_patient = Patient(
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        date_of_birth=date_of_birth,
        contact_number=contact_number,
        email=email,
        address=address,
    )
    db.add(new_patient)
    db.commit()
    return RedirectResponse("/patients", status_code=302)


# Route: Display all patients
@app.get("/patients", response_class=HTMLResponse)
def read_patients(request: Request, db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    return templates.TemplateResponse("index.html", {"request": request, "patients": patients})

# Route: Update a patient
@app.post("/patients/update/{patient_id}", response_class=HTMLResponse)
def update_patient(
    patient_id: int,
    first_name: str = Form(...),
    last_name: str = Form(...),
    gender: str = Form(...),
    date_of_birth: str = Form(...),
    contact_number: str = Form(...),
    email: str = Form(...),
    address: str = Form(...),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient.first_name = first_name
    patient.last_name = last_name
    patient.gender = gender
    patient.date_of_birth = date_of_birth
    patient.contact_number = contact_number
    patient.email = email
    patient.address = address
    db.commit()
    return RedirectResponse("/patients", status_code=302)

# Route: Delete a patient
@app.post("/patients/delete/{patient_id}", response_class=HTMLResponse)
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(patient)
    db.commit()
    return RedirectResponse("/patients", status_code=302)

# # Route to get a specific patient by ID
# @app.get("/patients/{patient_id}", response_model=PatientOut)
# def get_patient(patient_id: int, db: Session = Depends(get_db)):
#     db_patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
#     if db_patient is None:
#         raise HTTPException(status_code=404, detail="Patient not found")
#     return db_patient
