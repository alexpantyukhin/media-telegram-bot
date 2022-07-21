FROM python:3.7

WORKDIR /src

RUN apt update

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONPATH="$PYTHONPATH:/src"

COPY . /src