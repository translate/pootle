Front-end Development
=====================

Parts of Pootle front-end development require a Node.js run-time and packages
installed via `npm<https://www.npmjs.org/>`_.  This is only the case for
developing or building Pootle.


Setting Things Up
-----------------

In order to setup the front-end development enviroment, it's necessary to have
Node.js installed. Please check the `installation instructions for your
OS<http://nodejs.org/download/>`_.

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

Webpack-related configuration lives in *pootle/static/js/webpack.config.js*, so
in order to execute webpack commands successfully it's necessary either to:

  - Point webpack to the configuration file:
    `--config=pootle/static/js/webpack.config.js`,  or
  - `cd` into the root *js* directory.

The following examples will assume the latter for simplicity.

While in development, it's desired to create incremental builds while watching
file changes.

..code-block::bash

  $ webpack --watch

If you want to enable source maps in the development build for debugging,
just add the `-d` flag.

..code-block::bash

  $ webpack -d --watch

For creating a production-ready build, use:

..code-block::bash

  $ NODE_ENV=production webpack -p

This will also run the output through
`UglifyJS<https://github.com/mishoo/UglifyJS2>`_, making the output build
considerably lighter in size.

As an alternative to the previous step, you can use ``make assets`` from the
root of the repository clone, which will make all the static assets ready for
production use.
