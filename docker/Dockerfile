# translate/pootle:base
#
# VERSION       0.0.1

ARG BUILD_FROM=debian:stretch-slim


# Root stage shared by builder and app images
FROM $BUILD_FROM as root

MAINTAINER Ryan Northey <ryan@synca.io>

ARG APP_USER_ID=1000
ARG APP_GROUP_ID=1000
ARG APP_USERNAME=pootle
ARG APP_DIR=/app

ENV DEBIAN_FRONTEND=noninteractive \
    APP_DIR=$APP_DIR \
    APP_SRC_DIR=$APP_DIR/src/pootle \
    APP_SCRIPTS_DIR=$APP_DIR/src/pootle/docker/bin \
    APP_USER_ID=$APP_USER_ID \
    APP_GROUP_ID=$APP_GROUP_ID \
    APP_USERNAME=$APP_USERNAME

COPY ./root /tmp/build
RUN /tmp/build/install-root


# Build stage
FROM root as builder

COPY ./builder /tmp/build
RUN /tmp/build/install-build-env
RUN su -c "bash /tmp/build/install-common" $APP_USERNAME

ARG APP_PKG=Pootle==2.9rc1
ARG APP_REQUIREMENTS=https://raw.githubusercontent.com/translate/pootle/master/requirements
ARG BUILD_IMAGE

RUN su -c "bash /tmp/build/install-virtualenv" $APP_USERNAME

ARG BUILD_INSTALL_PRE
ARG BUILD_INSTALL_PKGS

RUN /tmp/build/install-build

ARG BUILD_INSTALL_EGGS
ARG BUILD_INSTALL_SETTINGS=./settings.conf

COPY $BUILD_INSTALL_SETTINGS /tmp/settings.conf
RUN su -c "bash /tmp/build/install-eggs" $APP_USERNAME


# App stage
FROM root

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
EXPOSE 8000

COPY ./app /tmp/build
COPY ./bin /tmp/build/bin

RUN /tmp/build/install-app-common

ARG BASE_INSTALL_PRE
ARG BASE_INSTALL_PKGS

RUN /tmp/build/install-app

# the chown flag has to be hardcoded for now
COPY --chown=pootle:pootle --from=builder "$APP_DIR" "$APP_DIR"

ARG APP_DB_ENV
ARG BUILD_IMAGE
ENV APP_DB_ENV=$APP_DB_ENV \
    BUILD_IMAGE=$BUILD_IMAGE

RUN /tmp/build/post-install
