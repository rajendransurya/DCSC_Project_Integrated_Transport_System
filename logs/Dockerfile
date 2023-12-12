FROM python:3.6-alpine
LABEL MAINTAINER="PUT YOUR EMAIL HERE"

RUN  pip3 install redis python-dotenv

WORKDIR /srv
COPY    logs/logs.py /srv
CMD [ "python3", "logs.py"]