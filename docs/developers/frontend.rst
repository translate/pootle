Front-end Development
=====================

Parts of Pootle front-end development require a Node.js run-time and packages
installed via `npm <https://www.npmjs.com/>`_.  This is only the case for
developing or building Pootle.


Setting Things Up
-----------------

In order to setup the front-end development enviroment, it's necessary to have
Node.js installed. Please check the `installation instructions for your
OS <https://nodejs.org/download/>`_.

.. warning::

   If you are using versions provided by you system then you need at least *npm
   >= v1.4.3* for installation to work correctly. To upgrade, use ``[sudo]
   npm install npm@latest -g``.

Once Node.js is available, Pootle dependencies need to be installed.

.. code-block:: console

    $ cd pootle/static/js
    $ npm install


This will read the :file:`package.json` file and install the development
dependencies.


Building Scripts
----------------

Simply run:

.. code-block:: console

    (env) $ ./manage.py webpack --dev


This will make sure to build all the necessary scripts and create the
relevant bundles with source maps support. It will also watch for changes
in scripts so you don't need to constantly be running this.

For creating a production-ready build, use:

.. code-block:: console

    (env) $ ./manage.py webpack


This will also run the output through
`UglifyJS <https://github.com/mishoo/UglifyJS2>`_, making the output build
considerably lighter in size.

Note that this step is also done as part of the :command:`make assets` command,
so you may only want to run the latter.
