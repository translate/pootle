# translate/pootle:dev-mariadb
#
# VERSION       0.0.1

# Build stage
FROM translate/pootle:dev-build

COPY ./settings.conf /tmp/
RUN mkdir -p /usr/share/man/man1 /usr/share/man/man7 \
    && apt-get update -qq \
    && apt-get install -qq -y \
         --no-install-recommends \
         libmariadbclient-dev-compat
USER pootle
RUN bash -c " \
    cd "$INSTALL_DIR" \
           && . bin/activate \
           && pip install -q \
                 MySQL-python \
           && cp /tmp/settings.conf \
                 /home/pootle/pootle_env/pootle.conf"

# Mariadb dev
FROM translate/pootle:dev-base

ENV POOTLE_ENV=mariadb
RUN apt-get update -qq \
    && apt-get install -qq -y \
         --no-install-recommends \
         libmariadbclient18 \
         mariadb-client
COPY --chown=pootle:pootle --from=0 /home/pootle/ /home/pootle
