FROM balenalib/raspberrypi4-64-alpine-python:3.9.6-latest-run
MAINTAINER Tobias Schoch <tobias.schoch@vtxmail.ch>


COPY requirements.txt /

# Install dependencies
RUN pip install -r requirements.txt

COPY rpistatus /rpistatus
COPY mqtt.py /
COPY docker.py /
COPY main.py /

CMD ["python", "main.py"]
