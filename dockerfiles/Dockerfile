
FROM    ubuntu:xenial

ENV     LANG C.UTF-8
RUN     export DEBIAN_FRONTEND=noninteractive; \
        apt-get update && apt-get install -y --no-install-recommends \
            software-properties-common

RUN     export DEBIAN_FRONTEND=noninteractive; \
        add-apt-repository ppa:fkrull/deadsnakes && \
        apt-get update && apt-get install -y --no-install-recommends \
            python2.6 \
            python2.7 \
            python3.4 \
            python3.5 \
            pypy \
            curl

RUN     curl -Ls https://bootstrap.pypa.io/get-pip.py | python3
RUN     pip install \
            tox \
            yapyautotest

WORKDIR /work
