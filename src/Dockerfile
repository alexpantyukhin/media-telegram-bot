FROM python:3.7

WORKDIR /app
COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . /app

CMD python -u telegram-controller.py