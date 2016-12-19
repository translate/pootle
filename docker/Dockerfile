FROM debian:8
MAINTAINER Ovidiu-Florin BOGDAN "ovidiu.b13@gmail.com"

ENV INSTALL_DIR=~/pootle \
    POOTLE_VERSION='2.7.3' \
    USE_LOCALE='en_US.UTF-8'

# Update the image packages
RUN apt update && \
    apt dist-upgrade -y

# Install Pootle dependencies
RUN apt update \
    && DEBIAN_FRONTEND=noninteractive \
    apt install -y \
        build-essential \
        libxml2-dev \
        libxslt-dev \
        locales \
        python-dev \
        python-pip \
        sudo \
        zlib1g-dev \
    && apt clean \
    && rm -rf /var/lib/apt/lists/* /tmp* /var/tmp/* \
    && pip install --upgrade pip \
    && pip install virtualenv

# Set-up locale
RUN echo "$USE_LOCALE" >> /etc/locale.gen \
    && locale-gen \
    && update-locale LANG=$USE_LOCALE

RUN groupadd -r pootle \
    && useradd -m -d /home/pootle -k /etc/skel -s /bin/bash -g pootle pootle

USER pootle

# Set-up Pootle
RUN mkdir -p $INSTALL_DIR && cd $_ \
    && virtualenv . \
    && . bin/activate \
    && pip install 'Pootle==$POOTLE_VERSION' \
    && pootle init \
    && pootle migrate \
    && pootle initdb --no-rq \



