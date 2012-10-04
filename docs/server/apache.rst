.. _apache:

Running Pootle on Apache
========================

Running Pootle under Apache will improve performance, give you more
flexibility, and might be better for security. It is strongly recommended to
run Pootle under Apache or a similar web server.


.. _apache#mod_wsgi:

Apache with mod_wsgi
--------------------

For anything except the most trivial deployments it is best to use a database
server such as :ref:`installation#mysql` or PostgreSQL rather than the default SQLite, and
to install `memcached
<https://docs.djangoproject.com/en/dev/topics/cache/#memcached>`_ and configure
it in *settings/90-local.conf*.

Make sure to review your global Apache settings (something like
*/etc/apache2/httpd.conf* or */etc/httpd/conf/httpd.conf*) for the
server-pool settings. The default settings provided by Apache are too high for
running a web application like Pootle. The ideal settings depend heavily on
your hardware and the number of users you expect to have. A moderate server
with 1GB memory might set ``MaxClients`` to something like ``20`` (for
example).

Running Pootle under Apache requires `mod_wsgi
<http://code.google.com/p/modwsgi/>`_

You need to extract Pootle in a directory accessible to the *apache* user.

Make sure Apache has read access to all of Pootle's files and write access to
the *dbs* and *po* subdirectories.


.. _apache#configuration:

Configuration
^^^^^^^^^^^^^

.. code-block:: apache

    # point at the wsgi loader script
    WSGIScriptAlias /pootle /var/www/Pootle/wsgi.py

    # The following two optional lines enables "daemon mode" which limits
    # the number of processes and therefore also keeps memory use more predictable
    WSGIDaemonProcess pootle processes=2 threads=3 stack-size=1048576 maximum-requests=5000 inactivity-timeout=900 display-name=%{GROUP}
    WSGIProcessGroup pootle

    # directly serve static files like css and images, no need to go through mod_wsgi and django
    Alias /pootle/html /var/www/Pootle/html
    <Directory /var/www/Pootle/html>
    Order deny,allow
    Allow from all
    </Directory>

    # Allow downloading translation files directly
    Alias /pootle/export /var/www/Pootle/po
    <Directory /var/www/Pootle/po>
    Order deny,allow
    Allow from all
    </Directory>

More info :doc:`Django + Apache + mod_wsgi
<django:how-to-use-django-with-apache-and-mod-wsgi>`


.. _apache#.htaccess:

.htaccess
^^^^^^^^^

If you do not have access to the main Apache configuration, you should still be
able to configure things correctly using the *.htaccess* file.

`More information
<http://code.google.com/p/modwsgi/wiki/ConfigurationGuidelines>`_ on
configuring *mod_wsgi* (including *.htaccess*)


.. _apache#troubleshooting:

Troubleshooting
^^^^^^^^^^^^^^^

There have been reports that using *mod_mem_cache* might cause issues. If you
get this error::

    SystemError: NULL result without error in PyObject_Call

You should disable the *mod_mem_cache* module in your Apache configuration.
