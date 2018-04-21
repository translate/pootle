# translate/pootle:base
#
# VERSION       0.0.1

FROM nginx

MAINTAINER Ryan Northey <ryan@synca.io>

ENV DEBIAN_FRONTEND=noninteractive

COPY pootle.template /etc/nginx/conf.d/pootle.template
COPY start_nginx /usr/local/bin/start_nginx

RUN apt-get update -qq \
    && apt-get install \
        -y \
        -qq \
        --no-install-recommends \
        openssl \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && apt-get clean
