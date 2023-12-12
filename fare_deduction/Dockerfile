# Use the official Python image as the base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the fare_deduction directory into the container
COPY /fare_deduction .

# Copy the db package directory into the container
COPY db/ ./db


# Install dependencies for rfid_service
RUN pip install uuid jsonpickle flask redis requests psycopg2-binary python-dotenv psycopg-pool psycopg_pool psycopg-binary psycopg

# Expose the port where the rfid_service Flask app runs (Port 6000)
EXPOSE 6100

# Define environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the rfid_service Flask application
CMD ["python", "fare_deduction.py"]