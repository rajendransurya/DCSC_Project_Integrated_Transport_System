# Use the official Python image as the base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the fare_deduction directory into the container
COPY /fare_deduction .

# Copy the db package directory into the container
COPY db/ ./db

COPY ../.env /app

# Install dependencies for rfid_service
RUN pip install json uuid jsonpickle flask redis requests psycopg2-binary python-dotenv logging

# Expose the port where the rfid_service Flask app runs (Port 6000)
EXPOSE 6100

# Define environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the rfid_service Flask application
CMD ["python", "fare_deduction.py"]