FROM python:3.11.0a6-alpine3.15
WORKDIR /code
COPY requirement.txt /code
RUN pip install -r requirement.txt --no-cache-dir
COPY . /code
CMD python coding.py

