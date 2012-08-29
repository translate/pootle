.. _nginx:

Pootle under Nginx
==================

Running Pootle under a web server such as Nginx will improve performance. Also
see the page about :doc:`apache` that might help with ideas on reaching the
best performance with Pootle.

For more information about Nginx and WSGI, visit `Nginx's WSGI page
<http://wiki.nginx.org/NginxNgxWSGIModule>`_

A Pootle Web-translation server is made up of static and dynamic content. By
default Pootle serves all content, for low-latency purposes it is better to get
other webserver (like Apache, Lighttpd or Nginx in this example) to serve the
content that does not change, the static content. It is just the issue of low
latency and making the translation experience more interactive that calls you
to proxy through Nginx.  The following steps show you how to setup Pootle to
proxy through Nginx.


.. _nginx#running_pootle_with_nginx_fastcgi_setup:

Running Pootle with Nginx (FastCGI setup)
-----------------------------------------

Run Pootle as a FastCGI application::

    python ./manage.py runfcgi host=127.0.0.1 port=8080

There are more possible parameters available. See ::

    python ./manage.py help runfcgi

And add the following lines to your Nginx config file::

     server {
        listen  80;  # port and optionally hostname where nginx listens
        server_name  example.com translate.example.com; # names of your site
        # Change the values above to the appropriate values

        location ^~ /html/ {
            root /path/to/Pootle-2.1.0/;
        }

        location / {
            fastcgi_pass 127.0.0.1:8080;
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


.. _nginx#running_pootle_with_nginx_ubuntu:

Running Pootle with Nginx (Ubuntu)
----------------------------------

If you have installed Pootle with apt-get you can use nginx to serve the static
files and pass through to the Pootle server.

To start Pootle::

   /etc/init.d/pootle start

And in your nginx `sites-enabled/pootle.conf` you can add the following,
adjusting as necessary::

   server {
      listen  *:80;
      server_name  example.com translate.example.com; # names of your site

      location ^~ /html/ {
         root /usr/share/pootle/;
      }

      location / {
         # Ensure you have the correct port and the full domain name
         # This address will appear in registration emails
         proxy_pass http://yourfulldomainna.me:8080; 
         proxy_set_header  X-Real-IP  $remote_addr;
      }
   }
