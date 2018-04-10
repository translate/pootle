# translate/pootle:dev-base
#
# VERSION       0.0.1

FROM translate/pootle:dev-root

MAINTAINER Ryan Northey <ryan@synca.io>

ENV POOTLE_LOG_DIR="$INSTALL_DIR/var/logs"

COPY ./install-base /usr/local/bin
RUN ./usr/local/bin/install-base
COPY ./entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
EXPOSE 8000
