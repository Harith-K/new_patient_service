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
from fastapi.responses import RedirectResponse
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
    __tablename__ = "patients"
    patient_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(255), index=True)
    last_name = Column(String(255))
    gender = Column(String(255))
    date_of_birth = Column(Date)
    contact_number = Column(String(255))
    email = Column(String(255))
    address = Column(String(255))  # Updated to String(255)
    medical_history = Column(String(255), default="")  # Updated to String(255)
    prescriptions = Column(String(255), default="")  # Updated to String(255)
    lab_results = Column(String(255), default="")  # Updated to String(255)
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
    patient_id: Optional[int] = Form(None),
    first_name: str = Form(...),
    last_name: str = Form(...),
    gender: str = Form(...),
    date_of_birth: str = Form(...),
    contact_number: str = Form(...),
    email: str = Form(...),
    address: str = Form(...),
    medical_history: str = Form(""),
    prescriptions: str = Form(""),
    lab_results: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        if patient_id:
            # Update existing patient
            patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
            if not patient:
                raise HTTPException(status_code=404, detail="Patient not found")
            
            patient.first_name = first_name
            patient.last_name = last_name
            patient.gender = gender
            patient.date_of_birth = datetime.datetime.strptime(date_of_birth, "%Y-%m-%d").date()
            patient.contact_number = contact_number
            patient.email = email
            patient.address = address
            patient.medical_history = medical_history
            patient.prescriptions = prescriptions
            patient.lab_results = lab_results
            db.commit()
            logging.info(f"Patient with ID {patient_id} updated successfully.")
        else:
            # Add new patient
            new_patient = Patient(
                first_name=first_name,
                last_name=last_name,
                gender=gender,
                date_of_birth=datetime.datetime.strptime(date_of_birth, "%Y-%m-%d").date(),
                contact_number=contact_number,
                email=email,
                address=address,
                medical_history=medical_history,
                prescriptions=prescriptions,
                lab_results=lab_results,
            )
            db.add(new_patient)
            db.commit()
            logging.info(f"New patient added successfully.")
        
        return RedirectResponse("/patients", status_code=302)
    except Exception as e:
        logging.error(f"Error adding/updating patient: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")


# Route: Display all patients
@app.get("/patients", response_class=HTMLResponse)
def read_patients(request: Request, db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    return templates.TemplateResponse("index.html", {"request": request, "patients": patients})

# Route: Update a patient
@app.get("/patients/add", response_class=HTMLResponse)
def get_patient_to_edit(patient_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Handles pre-filling the form for editing a patient.
    """
    patient_data = {}
    if patient_id:
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        patient_data = {
            "patient_id": patient.patient_id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "gender": patient.gender,
            "date_of_birth": patient.date_of_birth.isoformat(),
            "contact_number": patient.contact_number,
            "email": patient.email,
            "address": patient.address,
            "medical_history": patient.medical_history,
            "prescriptions": patient.prescriptions,
            "lab_results": patient.lab_results,
        }

    return templates.TemplateResponse("index.html", {"request": {}, "patient_data": patient_data, "patients": db.query(Patient).all()})

# Route: Delete a patient
@app.post("/patients/delete/{patient_id}", response_class=HTMLResponse)
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    try:
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            logging.warning(f"Attempt to delete non-existent patient ID: {patient_id}")
            raise HTTPException(status_code=404, detail="Patient not found")
        db.delete(patient)
        db.commit()
        logging.info(f"Patient with ID {patient_id} deleted successfully.")
        return RedirectResponse("/patients", status_code=302)
    except Exception as e:
        logging.error(f"Error deleting patient with ID {patient_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")

# # Route to get a specific patient by ID
# @app.get("/patients/{patient_id}", response_model=PatientOut)
# def get_patient(patient_id: int, db: Session = Depends(get_db)):
#     db_patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
#     if db_patient is None:
#         raise HTTPException(status_code=404, detail="Patient not found")
#     return db_patient
