# translate/pootle:dev-sqlite
#
# VERSION       0.0.1

# Build stage
FROM translate/pootle:build

COPY ./settings.conf /tmp/
RUN cp /tmp/settings.conf /home/pootle/pootle_env/pootle.conf

# Sqlite dev
FROM translate/pootle:base

ENV POOTLE_ENV=sqlite
RUN apt-get update -qq \
    && apt-get install -qq -y \
         --no-install-recommends \
         sqlite3
COPY --chown=pootle:pootle --from=0 /home/pootle/ /home/pootle
