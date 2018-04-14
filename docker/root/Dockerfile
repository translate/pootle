# translate/pootle:root
#
# VERSION       0.0.1

FROM debian:stretch-slim

MAINTAINER Ryan Northey <ryan@synca.io>

ENV DEBIAN_FRONTEND=noninteractive \
    INSTALL_DIR=~/pootle_env

COPY ./install-root /usr/local/bin
RUN ./usr/local/bin/install-root
