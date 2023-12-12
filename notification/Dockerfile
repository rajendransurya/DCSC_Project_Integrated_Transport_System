FROM python:3.9-slim

WORKDIR /app

RUN pip install redis sendgrid python-dotenv


COPY notification/notification.py /app

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python3", "notification.py"]