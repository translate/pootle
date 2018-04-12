# translate/pootle:dev-postgres
#
# VERSION       0.0.1

# Build stage
FROM translate/pootle:build

COPY ./settings.conf /tmp/
RUN mkdir -p /usr/share/man/man1 /usr/share/man/man7 \
    && apt-get update -qq \
    && apt-get install -qq -y \
         --no-install-recommends \
         libpq-dev
USER pootle
RUN bash -c " \
    cd "$INSTALL_DIR" \
           && . bin/activate \
           && pip install -q \
                  psycopg2-binary \
           && cp /tmp/settings.conf \
                 /home/pootle/pootle_env/pootle.conf"

# Postgres dev
FROM translate/pootle:base

ENV POOTLE_ENV=postgres
RUN mkdir -p /usr/share/man/man1 /usr/share/man/man7 \
    && apt-get update -qq \
    && apt-get install -qq -y \
         --no-install-recommends \
         postgresql-client
COPY --chown=pootle:pootle --from=0 /home/pootle/ /home/pootle
COPY ./bin /home/pootle/pootle_env/src/pootle/docker/bin
