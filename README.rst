|logo| Pootle
=============

|chat| |build| |health| |coverage| |requirements|


.. Resources

`Docs <http://docs.translatehouse.org/projects/pootle/en/latest/>`_ |
`Changes <http://docs.translatehouse.org/projects/pootle/en/latest/releases/2.8.0.html>`_ |
`Issues <https://github.com/translate/pootle/issues>`_ |
`Community Support <https://gitter.im/translate/pootle>`_ |
`Contributing <https://github.com/translate/pootle/blob/master/CONTRIBUTING.rst>`_ |
`Development Channel <https://gitter.im/translate/dev>`_


`Pootle <http://pootle.translatehouse.org/>`_ is an online translation and
localization tool.  It works to lower the barrier of entry, providing tools to
enable teams to work towards higher quality while welcoming newcomers.


Pootle is a Server
------------------

Pootle is written in Python using the Django framework and therefore can be
installed on any web server that supports serving WSGI applications.

A number of translation projects for a number of languages can be hosted on
Pootle.  Teams can manage their files, permissions, projects, and translate
on-line.  Files can be downloaded for offline translation.


Getting started
---------------

The easiest way to get started is by using the docker demo. You will need docker
installed on your system, and to be running as a user with permissions to manage
docker.

As the docker compose configuration is stored in the pootle directory, you will
need ``git`` installed and ``pip`` for some minimal python dependencies to get
set up.


Virtualenv
----------

You can optionally use a virtualenv to install the python requirements. This
will make it easier to install and run as a user other than ``root``


Demo install
------------

First install the requirements

::

  git clone https://github.com/translate/pootle
  cd pootle
  pip install -r requirements/host.txt

You can now run the demo, using the ``makey`` command runner

::

  makey demo

This will take a few moments to pull the required docker images, and
once up you should be able to browse to your pootle server on
http://localhost:8000



Copying
-------

Pootle is released under the General Public License, version 3 or later. See
the `LICENSE <https://github.com/translate/pootle/blob/master/LICENSE>`_ file
for details.


.. |logo| image:: https://cdn.rawgit.com/translate/pootle/master/pootle/static/images/logo-color.svg
          :target: https://github.com/translate/pootle
          :align: bottom

.. |chat| image:: https://img.shields.io/gitter/room/translate/pootle.svg?style=flat-square
        :alt: Join the chat at https://gitter.im/translate/pootle
        :target: https://gitter.im/translate/pootle

.. |build| image:: https://img.shields.io/travis/translate/pootle/master.svg?style=flat-square
        :alt: Build Status
        :target: https://travis-ci.org/translate/pootle/branches

.. |health| image:: https://landscape.io/github/translate/pootle/master/landscape.svg?style=flat-square
        :target: https://landscape.io/github/translate/pootle/master
        :alt: Code Health

.. |coverage| image:: https://img.shields.io/codecov/c/github/translate/pootle/master.svg?style=flat-square
        :target: https://codecov.io/gh/translate/pootle/branch/master
        :alt: Test Coverage

.. |requirements| image:: https://img.shields.io/requires/github/translate/pootle/master.svg?style=flat-square
        :target: https://requires.io/github/translate/pootle/requirements/?branch=master
        :alt: Requirements
