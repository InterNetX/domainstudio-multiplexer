FROM python:3.9-alpine
WORKDIR /code
COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
RUN python3 setup.py sdist
COPY ./modules/* ./
CMD ["python3", "wsgatehandler.py"]
