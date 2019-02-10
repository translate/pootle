Frequently Asked Questions (FAQ)
================================

Caught out by a problem installing or running Pootle? We hope you'll find some
answers here.  Ideal candidates are specific installation issues that we can't
integrate into the main docs.  Feel free to provide updates with your own
findings.

Installation
------------

Does Pootle run under Python 3?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pootle does not, yet, support Python 3 but it definitely is a goal.

Our first priority has been cleaning up the code and getting onto the latest
version of Django.  We've achieved that with Pootle 2.8.0.

We also want to be Django warning free, we've also achieved that in Pootle
2.8.0.

All of these where needed to ease to migration to Python 3.

Currently, we're trying to eliminate Python 2 specific changes and we're coding
pylint checks to prevent any regression.

If you want to help make this happen sooner, patches are welcome.


ModuleNotFoundError: No module named 'syspath_override'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: pytb

    File "/home/pootle/env/lib/python3.6/site-packages/pootle/runner.py", line 19, in <module>
       import syspath_override  # noqa
     ModuleNotFoundError: No module named 'syspath_override'

You are running Pootle using Python 3, change your virtual environment to
Python 2 and try again.

Something like this will be needed to setup your virtual environment.

.. code-block:: console

   $ mkvirtualenv --python=/path/to/python2 pootle


locale.Error: unsupported locale setting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pootle assumes that you have the ``en_US.utf8`` locale installed on your
server.  If for some reason your server does not include this (viz. on minimal
server installs) then you need to install that locale.

On a Debian based server simply run:

.. code-block:: console

   $ sudo dpkg-reconfigure locales


Installing missing system dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pootle may require you to install additional system dependencies.  The majority
of these relate to the installation of lxml, required by Pootle for XLIFF and
other XML based support.

lxml requires compilation so we depend on build components as well as libraries
for ``libxml``, ``libxslt`` and Python.

On Debian based system the following will install all additional system requirements:

.. code-block:: console

   $ sudo apt-get install build-essential libxml2-dev libxslt-dev python-dev python-pip zlib1g-dev


What is the optimal size for translation files?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are too many variables to give a definitive numbers.

In terms of a servers ability to handle large files, this will depend on the
size or shape of the database, available system resources, the database
configuration and the activity on the site.

What is helpful to be aware of is that Pootle does work on a file level.  So
really large translation files might become unwieldy to process, and queries to
find untranslated units in the file may take longer then expected.

Our general advice is to keep related translations in the same file and this
should work fine.  If performance does appear to be a problem then break the
large files into logical divisions to create smaller files.
