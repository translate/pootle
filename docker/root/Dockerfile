# translate/pootle:root
#
# VERSION       0.0.1

FROM debian:stretch-slim

MAINTAINER Ryan Northey <ryan@synca.io>

ENV DEBIAN_FRONTEND=noninteractive \
    INSTALL_DIR=~/pootle_env \
    POOTLE_PKG=Pootle==2.9rc1 \
    POOTLE_LOG_DIR="$INSTALL_DIR/var/logs"

COPY ./install-root /usr/local/bin
COPY ./no-apt-cache /etc/apt/apt.conf.d/02nocache
RUN ./usr/local/bin/install-root
