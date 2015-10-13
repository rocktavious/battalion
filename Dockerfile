FROM python:2.7

RUN mkdir -p /src /out /data

RUN pip install \
  docopt==0.6.2 \
  pyul==0.4.5 \
  six==1.9.0 \
  pytest \
  pytest-cov \
  pytest-capturelog \
  flake8>=2.3.0 \

WORKDIR /src
COPY ./src/ /src

# This is to make pbr work
RUN git init
RUN python setup.py develop
