FROM python:3.9-slim-buster AS distro-base
WORKDIR /app/framework

RUN apt-get update && apt-get dist-upgrade -y
RUN apt-get install -y htop vim

RUN apt-get update

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

RUN pip install .

