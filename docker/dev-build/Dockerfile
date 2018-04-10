# translate/pootle:dev-build
#
# VERSION       0.0.1

FROM translate/pootle:dev-root

MAINTAINER Ryan Northey <ryan@synca.io>

COPY ./install-build /usr/local/bin
RUN ./usr/local/bin/install-build

USER pootle

COPY ./install-virtualenv /usr/local/bin
RUN  ./usr/local/bin/install-virtualenv

USER root
