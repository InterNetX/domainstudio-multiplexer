FROM python:3.9-alpine
WORKDIR /code
COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt
EXPOSE 8888
COPY . .
RUN python3 setup.py sdist
COPY ./modules/* ./
CMD ["python3", "clienthandler.py"]
