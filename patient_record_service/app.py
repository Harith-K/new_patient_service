from fastapi import FastAPI, HTTPException ,Depends
from pydantic import BaseModel ,validator
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Date, Text, JSON, TIMESTAMP
from sqlalchemy.orm import sessionmaker ,Session,relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime
import os
from dotenv import load_dotenv


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
    address = Column(Text)
    medical_history = Column(JSON)
    prescriptions = Column(JSON)
    lab_results = Column(JSON)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

  #######NEED TO WORK ON THE RELATIONSHIP########  
  # Define the reverse relationship for appointments
  #  appointments = relationship("appointment_scheduling_service.Appointment", back_populates="patient")  


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
@app.post("/patients/", response_model=PatientOut)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    db_patient = Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

# Route to get all patients
@app.get("/patients/", response_model=list[PatientOut])
def get_all_patients(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    return patients

# Route to get a specific patient by ID
@app.get("/patients/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    db_patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db_patient

@app.get("/patients/test/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    db_patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db_patient
