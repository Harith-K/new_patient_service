# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install python-dotenv to read environment variables from .env
RUN pip install python-dotenv

# Expose the port that the app runs on
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Load environment variables from .env file
# This ensures that your app reads the .env file at runtime
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]