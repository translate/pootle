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

A sample Apache configuration with mod_wsgi might look like this:

.. code-block:: apache

    # Point to the WSGI loader script
    WSGIScriptAlias /pootle /var/www/pootle/wsgi.py

    # The following two optional lines enables "daemon mode" which limits the
    # number of processes and therefore also keeps memory use more predictable
    WSGIDaemonProcess pootle processes=2 threads=3 stack-size=1048576 maximum-requests=5000 inactivity-timeout=900 display-name=%{GROUP}
    WSGIProcessGroup pootle

    # Directly serve static files like css and images, no need to go through
    # mod_wsgi and django
    Alias /pootle/assets /var/www/pootle/assets
    <Directory /var/www/Pootle/assets>
    Order deny,allow
    Allow from all
    </Directory>

    # Allow downloading translation files directly
    Alias /pootle/export /var/www/pootle/po
    <Directory /var/www/pootle/po>
    Order deny,allow
    Allow from all
    </Directory>

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

    $ python manage.py runfcgi host=127.0.0.1 port=8080

There are more possible parameters available. See::

    $ python manage.py help runfcgi

And add the following lines to your Nginx config file:

.. code-block:: nginx

   server {
      listen  80;  # port and optionally hostname where nginx listens
      server_name  example.com translate.example.com; # names of your site
      # Change the values above to the appropriate values

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
