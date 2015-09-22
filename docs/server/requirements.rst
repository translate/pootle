.. _requirements:

Pootle requirements
===================

.. _requirements#hardware:

Hardware Requirements
---------------------

Your Pootle installation will need to be flexible enough to handle the
translation load. The recommended hardware depends highly on the performance you
expect, the number of users you want to support, and the number and size of the
files you want to host.

Whatever hardware you have, you will still benefit from performance improvements
if you can :doc:`optimize your system <optimization>`.

Your disk space should always be enough to store your files and your Pootle
database, with some extra space available.


.. _requirements#system:

System Requirements
-------------------

To run Pootle you need a computer running:

- Linux
- Mac OS X

Or, any other Unix-like system.

.. note:: Pootle will not run on Windows since it uses RQ, whose workers cannot
   run on `Windows <http://python-rq.org/docs/>`_.

   Some developers do develop on Windows so these problems can be worked around
   for some of the development tasks.

   Pootle should be able to run on any system that implements ``fork()``.


.. _requirements#python:

Python version
--------------

**Python 2.7 is required**. 2.6 won't work, and 3.x is not supported.


.. _requirements#packages:

Installing system packages
--------------------------

You will need a C compiler and  the development libraries for Python and XML to
be available on your system before you will be able to install your virtual
environment. You will also need pip.

Eg. on a Debian-based system:

.. code-block:: bash

  $ sudo apt-get install build-essential libxml2-dev libxslt-dev python-dev python-pip

You will also need to access to a working Redis server to provide caching to
Pootle and for managing asynchronous workers.

To install and run Redis on a Debian-based system:

.. code-block:: bash

   $ sudo apt-get install redis-server
   $ sudo services redis-server start

.. note:: Pootle requires a minimum Redis server version of 2.8.4. If you are using
   Debian Wheezy you will need to install `redis-server` from backports.


.. _requirements#customize-static:

System requirements for customising static resources
----------------------------------------------------

In order to customise static resources such as CSS or JavaScript, you must
install Node.js and npm.

On a Debian-based system you can install these with:

.. code-block:: bash

   $ sudo apt-get install nodejs npm

On Debian Jessie and perhaps other distributions you also need to link the
``nodejs`` command to ``node``:

.. code-block:: bash

   $ sudo update-alternatives --install /usr/bin/node node /usr/bin/nodejs 99
