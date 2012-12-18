.. _apache:

Running under Apache
====================

Running Pootle under Apache will improve performance, give you more
flexibility, and might be better for security. It is strongly recommended to
run Pootle under Apache or a similar web server.


.. _apache#reverse_proxy:

Proxying with Apache
--------------------

If you want to reverse proxy through Apache, you will need to have `mod_proxy
<https://httpd.apache.org/docs/current/mod/mod_proxy.html>`_ installed for
forwarding requests and configure it accordingly.

.. code-block:: apache

    ProxyPass / http://localhost:8000/
    ProxyPassReverse / http://localhost:8000/


.. _apache#mod_wsgi:

Apache with mod_wsgi
--------------------

Make sure to review your global Apache settings (something like
*/etc/apache2/httpd.conf* or */etc/httpd/conf/httpd.conf*) for the server-pool
settings. The default settings provided by Apache are too high for running a web
application like Pootle. The ideal settings depend heavily on your hardware and
the number of users you expect to have. A moderate server with 1GB memory might
set ``MaxClients`` to something like ``20``, for example.

Make sure Apache has read access to all of Pootle's files and write access to
the :setting:`PODIRECTORY` directory.


.. _apache#configuration:

Configuration
^^^^^^^^^^^^^

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
^^^^^^^^^

If you do not have access to the main Apache configuration, you should still be
able to configure things correctly using the *.htaccess* file.

`More information
<http://code.google.com/p/modwsgi/wiki/ConfigurationGuidelines>`_ on
configuring *mod_wsgi* (including *.htaccess*)
