FROM python:3.11-alpine
WORKDIR /sayanbot
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
