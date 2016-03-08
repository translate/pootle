.. _web:

Running under a Web Server
==========================

Running Pootle with a front end web server will improve performance, give you
more flexibility, and might be better for security. It is strongly recommended
to run Pootle under Apache, Nginx, or a similar web server.


.. _pootle#running_as_a_service:

Running Pootle and RQ workers as a Service
------------------------------------------

If you plan to run Pootle and/or RQ workers as system services, you can use
whatever software you are familiar with for that purpose. For example
`Supervisor <http://supervisord.org/>`_, `Circus
<http://circus.readthedocs.org/en/latest/>`_ or `daemontools
<http://cr.yp.to/daemontools.html>`_ might fit your needs.


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
    ProxyPreserveHost On


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
the :setting:`POOTLE_TRANSLATION_DIRECTORY` directory.

.. note:: Most of the paths present in the examples in this section are the
   result of deploying Pootle using a Python virtualenv as told in the
   :ref:`Setting up the Environment <installation#setup-environment>` section
   from the :ref:`Quickstart installation <installation>` instructions.

   If for any reason you have different paths, you will have to adjust the
   examples before using them.

   For example the path :file:`/var/www/pootle/env/lib/python2.7/site-packages/`
   will be different if you have another Python version, or if the Python
   virtualenv is located in any other place.


First it is necessary to create a WSGI loader script:

.. literalinclude:: apache-wsgi.py
   :language: python

Place it in :file:`/var/www/pootle/wsgi.py`. If you use a different location
remember to update the Apache configuration accordingly.

A sample Apache configuration with mod_wsgi might look like this:

.. literalinclude:: apache-virtualhost.conf
   :language: apache

You can find more information in the `Django docs about Apache and
mod_wsgi <https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/modwsgi/>`_.


.. _apache#.htaccess:

.htaccess
"""""""""

If you do not have access to the main Apache configuration, you should still be
able to configure things correctly using the *.htaccess* file.

`More information
<https://code.google.com/archive/p/modwsgi/wikis/ConfigurationGuidelines.wiki>`_
on configuring *mod_wsgi* (including *.htaccess*)


.. _nginx:

Running under Nginx
-------------------

Running Pootle under a web server such as Nginx will improve performance. For
more information about Nginx and WSGI, visit `Nginx's WSGI module page
<http://nginx.org/en/docs/http/ngx_http_uwsgi_module.html>`_

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
