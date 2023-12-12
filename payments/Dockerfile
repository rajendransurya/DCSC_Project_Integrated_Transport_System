FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the rfid_service directory into the container
COPY payments/ .

# Copy the db package directory into the container
COPY db/ ./db


# Install dependencies for rfid_service
RUN pip install flask requests jsonpickle psycopg2-binary python-dotenv psycopg-pool redis datetime psycopg_pool psycopg-binary psycopg

# Expose the port where the rfid_service Flask app runs (Port 6000)
EXPOSE 6200

# Define environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the rfid_service Flask application
CMD ["python", "payments.py"]