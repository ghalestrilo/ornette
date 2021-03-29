
# Ornette base image
FROM python:3.8-slim-buster

# Build Ornette Deps
RUN pip3 install --upgrade pip
RUN pip3 install python-osc

RUN mkdir /ornette
WORKDIR /ornette
EXPOSE 5005/udp

# Magenta (Python 3)
RUN apt-get update
RUN apt-get install -y build-essential libasound2-dev libjack-dev libsndfile1
RUN pip3 install magenta