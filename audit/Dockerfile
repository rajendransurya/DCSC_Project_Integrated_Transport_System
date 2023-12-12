FROM python:3.9-slim

WORKDIR /app

RUN pip install boto3 redis python-dotenv


COPY audit/audit.py /app

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python3", "audit.py"]