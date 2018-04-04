.. _docker:

Docker
======

You can install a development and test environment using docker.


.. _docker#assumptions:


Assumptions
-----------

- You have docker installed and working on your system
- The user you are using has permissions to use docker


.. _docker#virtualenv:

Create a virtualenv (optional)
------------------------------

Installing with virtualenv keeps your host environment clean, and separates
your development environment from the host.

For example:

.. code-block:: console

  $ mkvirtualenv pootle
  $ cd ~/virtualenvs/pootle


.. _docker#clone:

Clone the pootle repository
---------------------------

You most likely want to clone *your* fork of the pootle repository, so you
can easily create Pull Requests for your changes.

.. code-block:: console

  (pootle): git clone git@github.com:$USER/pootle
  (pootle): cd pootle/


.. _docker#requirements:

Install host requirements
-------------------------

.. code-block:: console

  (pootle): pip install -r requirements/host.txt


.. _docker#install:

Install the pootle database
---------------------------

The default installer will create a postgresql database with

.. code-block:: console

  (pootle): makey install-dev

This will take some time as it loads the default projects


.. _docker#server:

Run the development server
--------------------------

Once Pootle is installed you can run the development server with

.. code-block:: console

  (pootle): makey runserver
