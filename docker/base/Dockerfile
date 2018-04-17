# translate/pootle:base
#
# VERSION       0.0.1

ARG BUILD_FROM=translate/pootle:build
ARG BASE_FROM=translate/pootle:root

# Build stage
FROM $BUILD_FROM

ARG BUILD_INSTALL_EGGS
ARG BUILD_INSTALL_PRE
ARG BUILD_INSTALL_PKGS
ARG BUILD_INSTALL_SETTINGS=./settings.conf

COPY ./install-build /usr/local/bin
COPY ./install-virtualenv /usr/local/bin
RUN ./usr/local/bin/install-build
COPY $BUILD_INSTALL_SETTINGS /tmp/settings.conf
USER pootle
RUN ./usr/local/bin/install-virtualenv

# Product stage
FROM $BASE_FROM

ARG BASE_INSTALL_PRE
ARG BASE_INSTALL_PKGS
ARG POOTLE_ENV
ARG BUILD_IMAGE

ENV POOTLE_ENV=$POOTLE_ENV
ENV BUILD_IMAGE=$BUILD_IMAGE

COPY . /tmp/build

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
EXPOSE 8000

RUN ./tmp/build/install-base
COPY --chown=pootle:pootle --from=0 /home/pootle/ /home/pootle
RUN ./tmp/build/post-install
