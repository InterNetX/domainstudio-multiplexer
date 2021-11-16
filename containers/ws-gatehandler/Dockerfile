FROM python:3.9
WORKDIR /code
COPY ./containers/ws-gatehandler/requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY ./utilities/* ./containers/ws-gatehandler/redisqueue
COPY ./containers/ws-gatehandler ./containers/ws-gatehandler
WORKDIR ./containers/ws-gatehandler
CMD ["python3", "wsgatehandler.py"]
