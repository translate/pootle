# translate/pootle:base
#
# VERSION       0.0.1

ARG BUILD_FROM=debian:stretch-slim


# Root stage shared by builder and produced images
FROM $BUILD_FROM as root

MAINTAINER Ryan Northey <ryan@synca.io>

ENV DEBIAN_FRONTEND=noninteractive \
    INSTALL_DIR=~/pootle_env

COPY ./root /tmp/build
RUN /tmp/build/install-root


# Build stage
FROM root as builder

COPY ./builder /tmp/build
RUN /tmp/build/install-build-env

ARG POOTLE_PKG=Pootle==2.9rc1
ARG POOTLE_REQUIREMENTS=https://raw.githubusercontent.com/translate/pootle/master/requirements
ARG POOTLE_ENV
ARG BUILD_IMAGE
ENV POOTLE_ENV=$POOTLE_ENV
ENV BUILD_IMAGE=$BUILD_IMAGE
ARG BUILD_INSTALL_EGGS
ARG BUILD_INSTALL_PRE
ARG BUILD_INSTALL_PKGS
ARG BUILD_INSTALL_SETTINGS=./settings.conf

RUN /tmp/build/install-build
COPY $BUILD_INSTALL_SETTINGS /tmp/settings.conf
RUN su -c "bash /tmp/build/install-virtualenv" pootle


# Product stage
FROM root

ARG BASE_INSTALL_PRE
ARG BASE_INSTALL_PKGS
ARG POOTLE_ENV
ARG BUILD_IMAGE

ENV POOTLE_ENV=$POOTLE_ENV
ENV BUILD_IMAGE=$BUILD_IMAGE

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
EXPOSE 8000

COPY . /tmp/build

RUN /tmp/build/install-base
COPY --chown=pootle:pootle --from=builder /home/pootle/ /home/pootle
RUN /tmp/build/post-install
