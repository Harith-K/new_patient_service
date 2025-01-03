# Dockerfile for appointment_scheduling_service

# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the entire project folder (including patient_record_service)
COPY ../ /app/

# Install dependencies for appointment scheduling service
RUN pip install --no-cache-dir -r /app/appointment_scheduling_service/requirements.txt

# Install dependencies for patient record service
RUN pip install --no-cache-dir -r /app/patient_record_service/requirements.txt


# Add patient_record_service to PYTHONPATH to make it available for import
ENV PYTHONPATH="${PYTHONPATH}:/app/patient_record_service"

# Install python-dotenv to read environment variables from .env
RUN pip install python-dotenv

# Expose the port the app runs on
EXPOSE 5001

# Run the FastAPI application
CMD ["uvicorn", "appointment_scheduling_service.app:app", "--host", "0.0.0.0", "--port", "5001"]
