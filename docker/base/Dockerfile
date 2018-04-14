# translate/pootle:base
#
# VERSION       0.0.1

FROM translate/pootle:root

MAINTAINER Ryan Northey <ryan@synca.io>

COPY ./install-base /usr/local/bin
RUN ./usr/local/bin/install-base
COPY ./entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
EXPOSE 8000
