# FROM tensorflow/magenta
FROM python:3.8-slim-buster

# Build Ornette Deps
RUN pip3 install --upgrade pip
RUN pip3 install python-osc

RUN apt-get update
RUN apt-get install -y build-essential libasound2-dev libjack-dev
RUN pip3 install magenta