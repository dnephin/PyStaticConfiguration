
FROM    ubuntu:xenial

ENV     LANG C.UTF-8
RUN     export DEBIAN_FRONTEND=noninteractive; \
        apt-get update && apt-get install -y --no-install-recommends \
            software-properties-common

RUN     export DEBIAN_FRONTEND=noninteractive; \
        add-apt-repository ppa:deadsnakes/ppa && \
        apt-get update && apt-get install -y --no-install-recommends \
            python3.6 \
            python3.7 \
            python3.8 \
            pypy3 \
            curl

RUN     curl -Ls https://bootstrap.pypa.io/get-pip.py | python3
RUN     pip install \
            tox \
            yapyautotest

WORKDIR /work
