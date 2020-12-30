FROM python:3.9-alpine
WORKDIR /code
COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
COPY ./modules/redisqueue.py .
CMD ["python3", "ws-gate-handler.py"]
