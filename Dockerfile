# This Dockerfile can be used to build lilvlib using:
# - Ubuntu 14.04 (Trusty)
# - Python 3.4

FROM ubuntu:14.04

MAINTAINER Alexandre Cunha <ale@moddevices.com>

# update and upgrade system
RUN apt-get update \
    && apt-get upgrade -qy \
    && apt-get install -qy ssh \
    && apt-get clean

RUN mkdir /root/.ssh
RUN touch /root/.ssh/known_hosts
RUN ssh-keyscan github.com >> /root/.ssh/known_hosts

RUN apt-get install -qy git libpcre3-dev devscripts \
    build-essential pkg-config swig debhelper \
    python3-all-dev python3-numpy python3-pip && apt-get clean

COPY . /lilvlib
WORKDIR /lilvlib

RUN ./build-python3-lilv.sh

RUN pip3 wheel -w wheelhouse .
