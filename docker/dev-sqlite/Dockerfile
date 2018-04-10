# translate/pootle:dev-sqlite
#
# VERSION       0.0.1

# Build stage
FROM translate/pootle:dev-build

COPY ./settings.conf /tmp/
RUN cp /tmp/settings.conf /home/pootle/pootle_env/pootle.conf

# Sqlite dev
FROM translate/pootle:dev-base

ENV POOTLE_ENV=sqlite
RUN apt-get update -qq \
    && apt-get install -qq -y \
         --no-install-recommends \
         sqlite3
COPY --chown=pootle:pootle --from=0 /home/pootle/ /home/pootle
