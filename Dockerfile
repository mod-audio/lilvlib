# This Dockerfile can be used to build lilvlib using:
# - Ubuntu 18
# - Python 3.6

FROM moddevices/devtools:ub18-py36

LABEL Alexandre Cunha <ale@moddevices.com>

RUN mkdir /root/.ssh
RUN touch /root/.ssh/known_hosts
RUN ssh-keyscan github.com >> /root/.ssh/known_hosts

RUN apt-get install --no-install-recommends -qy libpcre3-dev \
    devscripts pkg-config swig debhelper python3-numpy \
    && apt-get clean

COPY . /lilvlib
WORKDIR /lilvlib

RUN ./build-python3-lilv.sh
RUN pip3 wheel -w wheelhouse .
