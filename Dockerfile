# translate/pootle
#
# VERSION	0.0.1

FROM debian:jessie

MAINTAINER Ryan Northey <ryan@synca.io>

RUN apt-get update && \
    apt-get install -y \
            python-pip \
	    libxml2-dev \
	    libxslt-dev \
	    python-dev \
	    zlib1g-dev \
	    build-essential \
	    redis-server \
	    sudo && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    pip install virtualenv && \
    groupadd -r pootle && \
    useradd -m \
            -d /home/pootle \
            -k /etc/skel \
            -s /bin/bash \
            -g pootle \
	    pootle && \
    /etc/init.d/redis-server start && \
    sudo -u pootle bash -c "\
    	 mkdir ~/dev/env -p && \
	 cd ~/dev/env && \
    	 virtualenv . && \
    	 . bin/activate && \
    	 pip install --upgrade pip && \
    	 pip install pootle && \
	 pootle init && \
    	 echo 'DEBUG=True' >> ~/.pootle/pootle.conf && \
    	 pootle migrate --noinput && \
    	 pootle initdb && \
	 echo \"from django.contrib.auth import get_user_model; \	       
	       	from allauth.account.models import EmailAddress; \
	       	user = get_user_model().objects.create_superuser('admin', 'admin@example.com', 'pootle'); \
	       	EmailAddress.objects.create(user=user, email='admin@example.com', primary=True, verified=True) \" \
	    | pootle shell"

CMD /etc/init.d/redis-server start && \
    sudo -u pootle bash -c "\
    	 cd ~/dev/env && \
	 . bin/activate && \
	 (pootle rqworker &) && \
	 (if [ ! -e "var/first-run" ]; \
	  then \
	       pootle refresh_stats_rq && \
               mkdir -p var && \
	       touch var/first-run; \
	  fi) && \
	 pootle runserver 0.0.0.0:8000"

EXPOSE 8000
