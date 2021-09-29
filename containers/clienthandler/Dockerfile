FROM python:3.9-alpine
EXPOSE ${PROXYPORT}
WORKDIR /code
COPY ./containers/clienthandler/requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY ./utilities/* ./containers/clienthandler/redisqueue
COPY ./containers/clienthandler ./containers/clienthandler
WORKDIR ./containers/clienthandler
CMD ["python3", "clienthandler.py"]
