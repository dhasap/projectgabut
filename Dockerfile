FROM python:3.10-slim

WORKDIR /azkurabot

RUN apt update && apt upgrade -y
COPY requirements.txt /requirements.txt

COPY . .

RUN pip3 install -U pip && pip3 install -U -r requirements.txt
CMD ["python3", "bot.py"]
