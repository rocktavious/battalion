FROM python:2.7

RUN mkdir -p /src
RUN mkdir -p /out
RUN mkdir -p /data
RUN mkdir -p /media

COPY ./src/test-requirements.txt /tmp/test-requirements.txt
RUN pip install -r /tmp/test-requirements.txt

COPY ./src/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

WORKDIR /src
COPY ./src/ /src

# This is to make pbr work
RUN git init
RUN python setup.py develop
