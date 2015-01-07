.. _installation:

Installation
============

.. warning::

  Pootle 2.6.x is not meant to be installed for new deployments, since it is
  meant to be only used as an intermediate step for upgrading older Pootle
  deployments to the newer Pootle releases.

  Please install Pootle 2.7.x or later instead.


.. _installation#hardware_requirements:

Hardware Requirements
---------------------

Your Pootle installation will need to be flexible enough to handle the
translation load. The recommended hardware depends highly on the performance you
expect, the number of users you want to support, and the number and size of the
files you want to host.

Whatever hardware you have, you will still benefit from performance improvements
if you can :doc:`optimize your system<optimization>`.

Your disk space should always be enough to store your files and your Pootle
database, with some extra space available.


.. _installation#setup_environment:

Setting up the Environment
--------------------------

In order to install Pootle you will first create a virtual environment. This
allows you to keep track of dependencies without messing up with system
packages. For that purpose you need to install the ``virtualenv`` package. You
might already have it, but in case you haven't:

.. code-block:: bash

  $ pip install virtualenv


Now create a virtual environment on your location of choice by issuing the
``virtualenv`` command:

.. code-block:: bash

  $ virtualenv /var/www/pootle/env/


This will copy the system's default Python interpreter into your environment.
For activating the virtual environment you must run the ``activate`` script:

.. code-block:: bash

  $ source /var/www/pootle/env/bin/activate


Every time you activate this virtual environment, the Python interpreter will
know where to look for libraries. Also notice the environment name will be
prepended to the shell prompt.
