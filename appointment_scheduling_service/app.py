from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, TIMESTAMP, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship ,Session
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime 
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

# Ensure DB_PORT is valid and is an integer
try:
    DB_PORT = int(DB_PORT)  # Convert to integer
except (TypeError, ValueError) as e:
    raise ValueError("DB_PORT is not set correctly. Please ensure it is a valid integer.") from e



#SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:root@localhost:3306/meditrack"
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Pydantic models for request/response validatio
class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_time: datetime
    status: str = "booked"  # Default status

class AppointmentOut(AppointmentCreate):
    appointment_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

        json_encoders = {
            datetime: lambda v: v.isoformat()  # Convert datetime to ISO 8601 format
        }


# SQLAlchemy models for database interaction
class Appointment(Base):
    __tablename__ = "appointments"
    appointment_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer)  # ForeignKey referencing the patients table    ##FK-     , ForeignKey('patients.patient_id')
    doctor_id = Column(Integer)
    appointment_time = Column(TIMESTAMP, default=datetime.utcnow)
    status = Column(String(255), default="booked")
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Establish a relationship between Appointment and Patient (Patient is already defined in your database)
    #patient = relationship("patient_record_service.Patient", back_populates="appointments")


# Create the appointments table, but don't recreate the patients table
Base.metadata.create_all(bind=engine)

from patient_record_service.app import Patient

# # Add back_populates to the Patient model to establish the reverse relationship (this part is already in the Patient Record Service)
#Patient.appointments = relationship("Appointment", back_populates="patient")
#Appointment.patient = relationship("Patient", back_populates="appointments")


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Add back_populates to the Patient model to establish the reverse relationship (this part is already in the Patient Record Service)
#Patient.appointments = relationship("Appointment", back_populates="patient")

# API Endpoints

# Endpoint to create a new appointment
@app.post("/appointments/", response_model=AppointmentOut)
def create_appointment(appointment: AppointmentCreate, db: Session = Depends(get_db)):
    db_patient = db.query(Patient).filter(Patient.patient_id == appointment.patient_id).first()
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    db_appointment = Appointment(**appointment.dict())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

# Endpoint to retrieve an appointment by appointment_id
@app.get("/appointments/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    db_appointment = db.query(Appointment).filter(Appointment.appointment_id == appointment_id).first()
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return db_appointment

# Endpoint to retrieve appointments for a specific doctor
@app.get("/appointments/doctor/{doctor_id}", response_model=list[AppointmentOut])
def get_appointments_by_doctor(doctor_id: int, db: Session = Depends(get_db)):
    db_appointments = db.query(Appointment).filter(Appointment.doctor_id == doctor_id).all()
    return db_appointments

# Endpoint to update the status of an appointment
@app.put("/appointments/{appointment_id}", response_model=AppointmentOut)
def update_appointment_status(appointment_id: int, status: str, db: Session = Depends(get_db)):
    db_appointment = db.query(Appointment).filter(Appointment.appointment_id == appointment_id).first()
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    db_appointment.status = status
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

# Endpoint to cancel an appointment
@app.delete("/appointments/{appointment_id}", response_model=AppointmentOut)
def cancel_appointment(appointment_id: int, db: Session = Depends(get_db)):
    db_appointment = db.query(Appointment).filter(Appointment.appointment_id == appointment_id).first()
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    db_appointment.status = "canceled"
    db.commit()
    db.refresh(db_appointment)
    return db_appointment
