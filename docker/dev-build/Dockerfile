# translate/pootle:dev-build
#
# VERSION       0.0.1

FROM translate/pootle:root

MAINTAINER Ryan Northey <ryan@synca.io>

ARG POOTLE_REQUIREMENTS=https://raw.githubusercontent.com/translate/pootle/master/requirements

COPY ./install-build /usr/local/bin
RUN ./usr/local/bin/install-build

USER pootle

COPY ./install-virtualenv /usr/local/bin
RUN  ./usr/local/bin/install-virtualenv

USER root
