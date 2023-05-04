FROM ubuntu:jammy AS builder

RUN apt-get update && apt-get install -y build-essential software-properties-common libssl-dev libffi-dev
RUN apt-get update && apt-get install -y python3 pkg-config python3-dev python3-pip


# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

ADD . ./

RUN pip3 install -r requirements.txt

COPY . /root

WORKDIR /root

ENV GITHUB_TOKEN $GITHUB_TOKEN

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
CMD gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
