.. _web:

Running under a Web Server
==========================

Running Pootle under a proper web server will improve performance, give you more
flexibility, and might be better for security. It is strongly recommended to
run Pootle under Apache, Nginx, or a similar web server.


.. _apache:

Running under Apache
--------------------

You can use Apache either as a reverse proxy or straight with mod_wsgi.


.. _apache#reverse_proxy:

Proxying with Apache
^^^^^^^^^^^^^^^^^^^^

If you want to reverse proxy through Apache, you will need to have `mod_proxy
<https://httpd.apache.org/docs/current/mod/mod_proxy.html>`_ installed for
forwarding requests and configure it accordingly.

.. code-block:: apache

    ProxyPass / http://localhost:8000/
    ProxyPassReverse / http://localhost:8000/


.. _apache#mod_wsgi:

Apache with mod_wsgi
^^^^^^^^^^^^^^^^^^^^

Make sure to review your global Apache settings (something like
*/etc/apache2/httpd.conf* or */etc/httpd/conf/httpd.conf*) for the server-pool
settings. The default settings provided by Apache are too high for running a web
application like Pootle. The ideal settings depend heavily on your hardware and
the number of users you expect to have. A moderate server with 1GB memory might
set ``MaxClients`` to something like ``20``, for example.

Make sure Apache has read access to all of Pootle's files and write access to
the :setting:`PODIRECTORY` directory.

.. note:: Most of the paths present in the examples in this section are the
   result of deploying Pootle using a Python virtualenv as told in the
   :ref:`Setting up the Environment <installation#setup_environment>` section
   from the :ref:`Quickstart installation <installation>` instructions.

   If for any reason you have different paths, you will have to adjust the
   examples before using them.

   For example the path :file:`/var/www/pootle/env/lib/python2.7/site-packages/`
   will be different if you have another Python version, or if the Python
   virtualenv is located in any other place.


First it is necessary to create a WSGI loader script:

.. code-block:: python

    #!/usr/bin/env python
    # -*- coding: utf-8 -*-

    import os
    import site
    import sys


    # You probably will need to change these paths to match your deployment,
    # most likely because of the Python version you are using.
    ALLDIRS = [
        '/var/www/pootle/env/lib/python2.7/site-packages',
        '/var/www/pootle/env/lib/python2.7/site-packages/pootle/apps',
    ]

    # Remember original sys.path.
    prev_sys_path = list(sys.path)

    # Add each new site-packages directory.
    for directory in ALLDIRS:
        site.addsitedir(directory)

    # Reorder sys.path so new directories at the front.
    new_sys_path = []

    for item in list(sys.path):
        if item not in prev_sys_path:
            new_sys_path.append(item)
            sys.path.remove(item)

    sys.path[:0] = new_sys_path

    # Set the Pootle settings module as DJANGO_SETTINGS_MODULE.
    os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

    # Set the WSGI application.
    def application(environ, start_response):
        """Wrapper for Django's WSGIHandler().

        This allows to get values specified by SetEnv in the Apache
        configuration or interpose other changes to that environment, like
        installing middleware.
        """
        try:
            os.environ['POOTLE_SETTINGS'] = environ['POOTLE_SETTINGS']
        except KeyError:
            pass

        from django.core.wsgi import get_wsgi_application
        _wsgi_application = get_wsgi_application()
        return _wsgi_application(environ, start_response)


Place it in :file:`/var/www/pootle/wsgi.py`. If you use a different location
remember to update the Apache configuration accordingly.

A sample Apache configuration with mod_wsgi might look like this:

.. code-block:: apache

    WSGIRestrictEmbedded On
    WSGIPythonOptimize 1

    <VirtualHost *:80>
        # Domain for the Pootle server. Use 'localhost' for local deployments.
        #
        # If you want to deploy on example.com/your-pootle/ rather than in
        # my-pootle.example.com/ you will have to do the following changes to
        # this sample Apache configuration:
        #
        # - Change the ServerName directive to:
        #   ServerName example.com
        # - Change the WSGIScriptAlias directive to (note that /your-pootle must
        #   not end with a slash):
        #   WSGIScriptAlias /your-pootle /var/www/pootle/wsgi.py
        # - Change the Alias and Location directives for 'export', and the Alias
        #   directive for 'assets' to include the '/your-pootle'.
        # - Include the following setting in your custom Pootle settings:
        #   STATIC_URL = '/your-pootle/assets/'
        ServerName my-pootle.example.com

        # Set the 'POOTLE_SETTINGS' environment variable pointing at your custom
        # Pootle settings file.
        #
        # If you don't know which settings to include in this file you can use
        # the file '90-local.conf.sample' as a starting point. This file can be
        # found at '/var/www/pootle/env/lib/python2.7/site-packages/pootle/settings/'.
        #
        # Another way to specify your custom settings is to comment this
        # directive and add a new '90-local.conf' file (by copying the file
        # '90-local.conf.sample' and changing the desired settings) in
        # '/var/www/pootle/env/lib/python2.7/site-packages/pootle/settings/'
        # (default location for a pip-installed Pootle, having Python 2.7).
        #
        # This might require enabling the 'env' module.
        SetEnv POOTLE_SETTINGS /var/www/pootle/your_custom_settings.conf


        # The following two optional lines enable the "daemon mode" which
        # limits the number of processes and therefore also keeps memory use
        # more predictable.
        WSGIDaemonProcess pootle processes=2 threads=3 stack-size=1048576 maximum-requests=500 inactivity-timeout=300 display-name=%{GROUP} python-path=/var/www/pootle/env/lib/python2.7/site-packages
        WSGIProcessGroup pootle

        # Point to the WSGI loader script.
        WSGIScriptAlias / /var/www/pootle/wsgi.py

        # Turn off directory listing by default.
        Options -Indexes

        # Set expiration for some types of files.
        # This might require enabling the 'expires' module.
        ExpiresActive On

        ExpiresByType image/jpg "access plus 2 hours"
        ExpiresByType image/png "access plus 2 hours"

        ExpiresByType text/css "access plus 10 years"
        ExpiresByType application/x-javascript "access plus 10 years"

        # Optimal caching by proxies.
        # This might require enabling the 'headers' module.
        Header set Cache-Control "public"

        # gzip compression
        SetOutputFilter DEFLATE
        AddOutputFilterByType DEFLATE text/html text/css text/plain text/xml application/x-javascript

        # Directly serve static files like css and images, no need to go
        # through mod_wsgi and Django. For high performance consider having a
        # separate server.
        Alias /assets /var/www/pootle/env/lib/python2.7/site-packages/pootle/assets
        <Directory /var/www/pootle/env/lib/python2.7/site-packages/pootle/assets>
            Order deny,allow
            Allow from all
        </Directory>

        # Allow downloading translation files directly.
        # This location must be the same in the Pootle 'PODIRECTORY' setting.
        Alias /export /var/www/pootle/env/lib/python2.7/site-packages/pootle/po
        <Directory /var/www/pootle/env/lib/python2.7/site-packages/pootle/po>
            Order deny,allow
            Allow from all
        </Directory>

        <Location /export>
            # Compress before being sent to the client over the network.
            # This might require enabling the 'deflate' module.
            SetOutputFilter DEFLATE

            # Enable directory listing.
            Options Indexes
        </Location>

    </VirtualHost>


You can find more information in the `Django docs about Apache and
mod_wsgi <https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/modwsgi/>`_.


.. _apache#.htaccess:

.htaccess
"""""""""

If you do not have access to the main Apache configuration, you should still be
able to configure things correctly using the *.htaccess* file.

`More information
<http://code.google.com/p/modwsgi/wiki/ConfigurationGuidelines>`_ on
configuring *mod_wsgi* (including *.htaccess*)


.. _nginx:

Running under Nginx
-------------------

Running Pootle under a web server such as Nginx will improve performance. For
more information about Nginx and WSGI, visit `Nginx's WSGI page
<http://wiki.nginx.org/NginxNgxWSGIModule>`_

A Pootle server is made up of static and dynamic content. By default Pootle
serves all content, and for low-latency purposes it is better to get other
webserver to serve the content that does not change, the static content. It is
just the issue of low latency and making the translation experience more
interactive that calls you to proxy through Nginx.  The following steps show you
how to setup Pootle to proxy through Nginx.


.. _nginx#proxy:

Proxying with Nginx
^^^^^^^^^^^^^^^^^^^

The default Pootle server runs at port 8000 and for convenience and simplicity
does ugly things such as serving static files — you should definitely avoid that
in production environments.

By proxying Pootle through nginx, the web server will serve all the static media
and the dynamic content will be produced by the app server.

.. code-block:: nginx

   server {
      listen  80;
      server_name  pootle.example.com;

      access_log /path/to/pootle/logs/nginx-access.log;
      gzip on; # Enable gzip compression

      charset utf-8;

      location /assets {
          alias /path/to/pootle/env/lib/python2.6/site-packages/pootle/assets/;
          expires 14d;
          access_log off;
      }

      location / {
        proxy_pass         http://localhost:8000;
        proxy_redirect     off;

        proxy_set_header   Host             $host;
        proxy_set_header   X-Real-IP        $remote_addr;
        proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
      }
    }


.. _nginx#proxy_fastcgi:

Proxying with Nginx (FastCGI)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run Pootle as a FastCGI application::

    $ pootle runfcgi host=127.0.0.1 port=8080

There are more possible parameters available. See::

    $ pootle help runfcgi

And add the following lines to your Nginx config file:

.. code-block:: nginx

   server {
      listen  80;  # port and optionally hostname where nginx listens
      server_name  example.com translate.example.com; # names of your site
      # Change the values above to the appropriate values
      gzip on; # Enable gzip compression

      location ^~ /assets/ {
          root /path/to/pootle/;
      }

      location / {
          fastcgi_pass 127.0.0.1:8000;
          fastcgi_param QUERY_STRING $query_string;
          fastcgi_param REQUEST_METHOD $request_method;
          fastcgi_param CONTENT_TYPE $content_type;
          fastcgi_param CONTENT_LENGTH $content_length;
          fastcgi_param REQUEST_URI $request_uri;
          fastcgi_param DOCUMENT_URI $document_uri;
          fastcgi_param DOCUMENT_ROOT $document_root;
          fastcgi_param SERVER_PROTOCOL $server_protocol;
          fastcgi_param REMOTE_ADDR $remote_addr;
          fastcgi_param REMOTE_PORT $remote_port;
          fastcgi_param SERVER_ADDR $server_addr;
          fastcgi_param SERVER_PORT $server_port;
          fastcgi_param SERVER_NAME $server_name;
          fastcgi_pass_header Authorization;
          fastcgi_intercept_errors off;
          fastcgi_read_timeout 600;
      }
    }

.. note::

  The ``fastcgi_read_timeout`` line is only relevant if you're getting Gateway
  Timeout errors and you find them annoying. It defines how long (in seconds,
  default is 60) Nginx will wait for response from Pootle before giving up.
  Your optimal value will vary depending on the size of your translation
  project(s) and capabilities of the server.

.. note::

  Not all of these lines may be required. Feel free to remove those you find
  useless from this instruction.
