Front-end Development
=====================

Parts of Pootle front-end development require a Node.js run-time and packages
installed via `npm <https://www.npmjs.org/>`_.  This is only the case for
developing or building Pootle.


Setting Things Up
-----------------

In order to setup the front-end development enviroment, it's necessary to have
Node.js installed. Please check the `installation instructions for your
OS <http://nodejs.org/download/>`_.

Once Node.js is available, Pootle dependencies need to be installed.

..code-block::bash

  $ cd pootle/static/js
  $ npm install

This will read the `package.json` file and install the development
dependencies.

Afterwards Webpack needs to be installed system-wide. This tool allows to use
CommonJS/AMD style modules, and offers advanced ways to create client-side
builds.

..code-block::bash

  $ npm install -g webpack


Building Scripts
----------------

Simply run:

..code-block::bash

  (env) $ ./manage.py webpack --dev

This will make sure to build all the necessary scripts and create the
relevant bundles with source maps support. It will also watch for changes
in scripts so you don't need to constantly be running this.


For creating a production-ready build, use:

..code-block::bash

  (env) $ ./manage.py webpack

This will also run the output through
`UglifyJS <https://github.com/mishoo/UglifyJS2>`_, making the output build
considerably lighter in size.

Note that this step is also done as part of the ``make assets`` command,
so you may only want to run the latter.
