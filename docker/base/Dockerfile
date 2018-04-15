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

COPY $BUILD_INSTALL_SETTINGS /tmp/settings.conf

RUN (if [ ! -z "$BUILD_INSTALL_PRE" ]; \
        then \
          $BUILD_INSTALL_PRE; \
     fi) \
    && (if [ ! -z "$BUILD_INSTALL_PKGS" ]; \
          then \
              apt-get update -qq \
              && apt-get install -qq -y \
                      --no-install-recommends \
                    $BUILD_INSTALL_PKGS; \
        fi)

USER pootle
RUN bash -c " \
    cd "$INSTALL_DIR" \
      && (if [ ! -z "$BUILD_INSTALL_EGGS" ]; \
          then \
           . bin/activate \
           && pip install -q \
               $BUILD_INSTALL_EGGS; \
          fi) \
      && cp /tmp/settings.conf \
         /home/pootle/pootle_env/pootle.conf"

# Product stage
FROM $BASE_FROM

ARG BASE_INSTALL_PRE
ARG BASE_INSTALL_PKGS
ARG POOTLE_ENV

ENV POOTLE_ENV=$POOTLE_ENV

COPY ./install-base /usr/local/bin
COPY ./entrypoint.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
EXPOSE 8000

RUN ./usr/local/bin/install-base
COPY --chown=pootle:pootle --from=0 /home/pootle/ /home/pootle
