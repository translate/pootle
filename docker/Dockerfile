FROM python:2.7.12
MAINTAINER Ovidiu-Florin BOGDAN "ovidiu.b13@gmail.com"

ENV INSTALL_DIR=/pootle \
    CONFIG_DIR=/config \
    POOTLE_VERSION='2.7.6' \
    USE_LOCALE='en_US.UTF-8'

# Install Pootle dependencies
RUN apt update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt install -y \
            locales \
            ca-certificates
RUN apt update \
    && build_packages='\
        build-essential \
        libxml2-dev \
        libxslt-dev \
        python-dev \
        wget \
        zlib1g-dev' \
    && apt-get install \
        -s \
        $build_packages \
        | grep "Inst " \
        | cut -f 2 -d " " > build-deps.txt \
    && apt install -y $build_packages

# Set-up locale
RUN echo "$USE_LOCALE UTF-8" >> /etc/locale.gen \
    && locale-gen \
    && update-locale LANG=$USE_LOCALE

RUN groupadd -r pootle \
    && useradd -m -d /home/pootle -k /etc/skel -s /bin/bash -g pootle pootle

VOLUME /config

RUN mkdir -p $INSTALL_DIR

USER pootle
# Install Pootle
RUN cd $INSTALL_DIR \
    && virtualenv . \
    && . bin/activate \
    && pip install "Pootle==$POOTLE_VERSION"

USER root
# Clean image
RUN apt remove -y `cat build-deps.txt | tr "\n" " "` \
    && rm build-deps.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp* /var/tmp/*

USER pootle

COPY scripts/ /scripts/
COPY entrypoint.sh /
ENTRYPOINT /entrypoint.sh
