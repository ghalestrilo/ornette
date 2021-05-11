FROM pytorch/pytorch:0.4.1-cuda9-cudnn7-runtime


RUN pip install --upgrade pip
# RUN pip install music21
RUN pip install glog
RUN pip install python-osc pretty_errors mido pandas cython pyyaml

RUN pip install --ignore-installed PyYAML

RUN mkdir /ornette
WORKDIR /ornette
EXPOSE 5005/udp