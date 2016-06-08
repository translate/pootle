Making a Pootle Release
***********************

This page is divided in four sections. The first one lists the tasks that must
be performed before creating a package. The second section includes a list of
tasks to get a valid package. The third one to get the package published and
the release announced. The last one lists and suggests some possible cleanup
tasks to be done after releasing.

.. note:: Please note that this is not a complete list of tasks. Please feel
   free to improve it.


Pre-release tasks
=================

Before starting the release process it is necessary to perform some previous
tasks.


Upload and announce new translations
------------------------------------

We need to give localizers enough time to localize Pootle.  They need time to
do the actual translation and to feedback on any errors that they might
encounter.

First upload the new translations:

#. Create the new templates:

   .. code-block:: console

       $ git clone git@github.com:translate/pootle.git pootle-translations
       $ cd pootle-translations
       $ make pot


#. Upload the templates to Pootle for translation.
#. Update current translations against templates either on Pootle or in code
   and commits these updated files to Git.

Announce the new translations on the following channels:

- The News tab on Pootle -- for those not on any mailing list
- The translate-announce@lists.sourceforge.net and the
  translate-pootle@lists.sourceforge.net mailing lists -- for those who might
  miss the news.


String freeze
-------------

A string freeze would normally run between an RC and a final version. We want
to give a string freeze at least 2-4 weeks before a release. They must be
announced, explicitly stating the duration, on the
translate-announce@lists.sourceforge.net and the
translate-pootle@lists.sourceforge.net mailing lists.

.. note:: If we do have a string freeze break then announce it to people. The
   string freeze breaks usually are only allowed to fix mistakes on the
   translatable strings.


Create the package
==================

The first steps are to create and validate a package for the next release.


Get a clean checkout
--------------------

We work from a clean checkout to ensure that everything you are adding to the
build is what is in the repository and doesn't contain any of your uncommitted
changes. It also ensures that someone else could replicate your process.

.. code-block:: console

    $ git clone git@github.com:translate/pootle.git pootle-release
    $ cd pootle-release
    $ git submodule update --init


Update requirements versions
----------------------------

Update the minimum version number for the requirements in:

- :file:`requirements/`
- :file:`pootle/checks.py`
- :file:`docs/server/requirements.rst`


Make sure version numbers displayed on documentation examples match the latest
requirements on the above files.


Check copyright dates
---------------------

Update any copyright dates in :file:`docs/conf.py:copyright` and anywhere else
that needs fixing.

.. code-block:: console

    $ git grep 2013  # Should pick up anything that should be examined


Set build settings
------------------

Create :file:`~/.pootle/pootle_build.conf` with the following content:

.. code-block:: python

    #!/usr/bin/env python
    # -*- coding: utf-8 -*-

    """Configuration file to build Pootle.

    Must be placed in ~/.pootle/pootle_build.conf
    """

    # Django now requires to set some secret key to be set.
    SECRET_KEY = '__BuildingPootle_1234567890__'

    # Silence some checks so the build output is cleaner.
    SILENCED_SYSTEM_CHECKS = [
        'pootle.W004',  # Pootle requires a working mail server
        'pootle.W006',  # sqlite database backend is unsupported
        'pootle.W010',  # DEFAULT_FROM_EMAIL has default setting
        'pootle.W011',  # POOTLE_CONTACT_EMAIL has default setting
    ]


Update checks descriptions
--------------------------

The quality checks descriptions are kept as a static HTML page that has to be
regenerated in order to ensure the descriptions match the currently available
quality checks.

.. code-block:: console

    $ mkvirtualenv build-checks-templates
    (build-checks-templates)$ pip install -r requirements/build.txt
    (build-checks-templates)$ export POOTLE_SETTINGS=~/.pootle/pootle_build.conf
    (build-checks-templates)$ DJANGO_SETTINGS_MODULE=pootle.settings ./setup.py build_checks_templates
    (build-checks-templates)$ deactivate
    $ unset POOTLE_SETTINGS
    $ rmvirtualenv build-checks-templates


Update translations
-------------------

Update the translations from the `Pootle server
<http://pootle.locamotion.org/projects/pootle>`_

#. Download all translations

   .. code-block:: console

       $ make get-translations

#. Update :file:`pootle/locale/LINGUAS` to list the languages we would like to
   ship. While we package all PO files, this is an indication of which ones we
   want packagers to use.  The requirement is roughly 80% translated with no
   obvious variable errors. Languages with a small userbase can be included.

   .. code-block:: console

       $ make linguas

   Check the output and make any adjustments such as adding back languages that
   don't quite make the target but you wish to ship.

#. Build translations to check for errors:

   .. code-block:: console

       $ ./setup.py build_mo          # Build all LINGUAS enabled languages
       $ ./setup.py build_mo --check  # Not all of these are errors


Create release notes
--------------------

We create our release notes in reStructured Text, since we use that elsewhere
and since it can be rendered well in some of our key sites.

First we need to create a log of changes in Pootle, which is done generically
like this:

.. code-block:: console

    $ git log $previous_version..HEAD > docs/releases/$version.rst


Or a more specific example:

.. code-block:: console

    $ git log 2.5.0..HEAD > docs/releases/2.5.1.rst


Edit this file.  You can use the commits as a guide to build up the release
notes.  You should remove all log messages before the release.

.. note:: Since the release notes will be used in places that allow linking we
   use links within the notes.  These should link back to products websites
   (`Virtaal <http://virtaal.org>`_, `Pootle
   <http://pootle.translatehouse.org>`_, etc), references to `Translate
   <http://translatehouse.org>`_ and possibly bug numbers, etc.

Read for grammar and spelling errors.

.. note:: When writing the notes please remember:

   #. The voice is active. 'Translate has released a new version of Pootle',
      not 'A new version of Pootle was released by Translate'.
   #. The connection to the users is human not distant.
   #. We speak in familiar terms e.g. "I know you've been waiting for this
      release" instead of formal.

We create a list of contributors using this command:

.. code-block:: console

    $ git log 2.5.0..HEAD --format='%aN, ' | awk '{arr[$0]++} END{for (i in arr){print arr[i], i;}}' | sort -rn | cut -d\  -f2-


.. _releasing#up-version-numbers:

Up version numbers
------------------

Update the version number in:

- :file:`pootle/__init__.py:VERSION`
- Documentation examples, especially :file:`docs/server/installation.rst` and
  :file:`docs/server/upgrading.rst`

The version tuple should follow the pattern::

    (major, minor, micro, candidate, extra)

E.g. ::

    (1, 10, 0, 'final', 0)
    (2, 7, 0 'alpha', 1)

When in development we use 'alpha' with ``extra`` of 0.  The first release of a
``minor`` version will always have a ``micro`` of ``.0``. So ``2.6.0`` and
never just ``2.6``.


Install nvm
-----------

Most likely your system will provide a nodejs version older than the one that
is required. nvm is a tool that allows to quickly install and switch nodejs
versions.

Follow the `nvm installation instructions
<https://github.com/creationix/nvm#installation>`_.


Build the package
-----------------

Building is the first step to testing that things work. From your clean
checkout run:

.. code-block:: console

    $ mkvirtualenv build-pootle-release
    (build-pootle-release)$ nvm install 0.12  # Use nodejs 0.12
    (build-pootle-release)$ pip install --upgrade pip
    (build-pootle-release)$ pip install -r requirements/build.txt
    (build-pootle-release)$ export PYTHONPATH="${PYTHONPATH}:`pwd`"
    (build-pootle-release)$ export POOTLE_SETTINGS=~/.pootle/pootle_build.conf
    (build-pootle-release)$ ./setup.py build_mo --all  # If we are shipping an RC
    (build-pootle-release)$ make clean
    (build-pootle-release)$ make build
    (build-pootle-release)$ deactivate
    $ unset POOTLE_SETTINGS


This will create a tarball in :file:`dist/` which you can use for further
testing.

.. note:: We use a clean checkout just to make sure that no inadvertant changes
   make it into the release.


Test install and other tests
----------------------------

The easiest way to test is in a virtualenv. You can test the installation of
the new release using:

.. code-block:: console

    $ mkvirtualenv test-pootle-release
    (test-pootle-release)$ pip install --upgrade pip
    (test-pootle-release)$ pip install dist/Pootle-$version.tar.bz2
    (test-pootle-release)$ pip install MySQL-python
    (test-pootle-release)$ pootle init


You can then proceed with other tests such as checking:

#. Documentation is available in the package
#. Assets are available in the package
#. Quick SQLite installation check:

   .. code-block:: console

     (test-pootle-release)$ pootle migrate
     (test-pootle-release)$ pootle initdb
     (test-pootle-release)$ pootle runserver --insecure
     (test-pootle-release)$  # Browse to localhost:8000

#. MySQL installation check:

   #. Create a blank database on MySQL:

      .. code-block:: console

        mysql -u $db_user -p$db_password -e 'CREATE DATABASE `test-mysql-pootle` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;'

   #. Change the database settings in the settings file created by
      :djadmin:`pootle init <init>` (by default :file:`~/.pootle/pootle.conf`)
      to use this new MySQL database
   #. Run the following:

      .. code-block:: console

        (test-pootle-release)$ pootle migrate
        (test-pootle-release)$ pootle initdb
        (test-pootle-release)$ pootle runserver --insecure
        (test-pootle-release)$  # Browse to localhost:8000

   #. Drop the MySQL database you have created:

      .. code-block:: console

        mysql -u $db_user -p$db_password -e 'DROP DATABASE `test-mysql-pootle`;'

#. MySQL upgrade check:

   #. Download a database dump from `Pootle Test Data
      <https://github.com/translate/pootle-test-data>`_ repository
   #. Create a blank database on MySQL:

      .. code-block:: console

        mysql -u $db_user -p$db_password -e 'CREATE DATABASE `test-mysql-pootle` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;'

   #. Import the database dump into the MySQL database:

      .. code-block:: console

        mysql -u $db_user -p$db_password test-mysql-pootle < $db_dump_file

   #. Run the following:

      .. code-block:: console

        (test-pootle-release)$ pootle migrate
        (test-pootle-release)$ pootle runserver --insecure
        (test-pootle-release)$  # Browse to localhost:8000

   #. Drop the MySQL database you have created:

      .. code-block:: console

        mysql -u $db_user -p$db_password -e 'DROP DATABASE `test-mysql-pootle`;'

#. Check that the instructions in the :doc:`Installation guide
   </server/installation>` are correct
#. Check that the instructions in the :doc:`Upgrade guide </server/upgrading>`
   are correct
#. Check that the instructions in the :doc:`Hacking guide <hacking>` are
   correct
#. Meta information about the package is correct. This is stored in
   :file:`setup.py`, to see some options to display meta-data use:

   .. code-block:: console

       $ ./setup.py --help

   Now you can try some options like:

   .. code-block:: console

       $ ./setup.py --name
       $ ./setup.py --version
       $ ./setup.py --author
       $ ./setup.py --author-email
       $ ./setup.py --url
       $ ./setup.py --license
       $ ./setup.py --description
       $ ./setup.py --long-description
       $ ./setup.py --classifiers

   The actual long description is taken from :file:`/README.rst`.

Finally clean your test environment:

.. code-block:: console

    (test-pootle-release)$ deactivate
    $ rmvirtualenv test-pootle-release


Publish the new release
=======================

Once we have a valid package it is necessary to publish it and announce the
release.


Tag and branch the release
--------------------------

You should only tag once you are happy with your release as there are some
things that we can't undo. You can safely branch for a ``stable/`` branch
before you tag.

.. code-block:: console

    $ git checkout -b stable/2.6.0
    $ git push origin stable/2.6.0
    $ git tag -a 2.6.0 -m "Tag version 2.6.0"
    $ git push --tags


Release documentation
---------------------

We need a tagged release or branch before we can do this. The docs are
published on Read The Docs.

- https://readthedocs.org/dashboard/pootle/versions/

Use the admin pages to flag a version that should be published.  When we have
branched the stable release we use the branch rather then the tag i.e.
``stable/2.5.0`` rather than ``2.5.0`` as that allows any fixes of
documentation for the ``2.5.0`` release to be immediately available.

Change all references to docs in the Pootle code to point to the branched
version as apposed to the latest version.

.. FIXME we should do this with a config variable to be honest!

Deactivate documentation that is no longer applicable.


Publish on PyPI
---------------

.. - `Submitting Packages to the Package Index
  <http://wiki.python.org/moin/CheeseShopTutorial#Submitting_Packages_to_the_Package_Index>`_


.. note:: You need a username and password on `Python Package Index (PyPI)
   <https://pypi.python.org/pypi>`_ and have rights to the project before you
   can proceed with this step.

   These can be stored in :file:`$HOME/.pypirc` and will contain your username
   and password. A first run of:

   .. code-block:: console

       $ ./setup.py register

   will create such file. It will also actually publish the meta-data so only
   do it when you are actually ready.


Run the following to publish the package on PyPI:

.. code-block:: console

    $ workon build-pootle-release
    (build-pootle-release)$ nvm install 0.12  # Use nodejs 0.12
    (build-pootle-release)$ export PYTHONPATH="${PYTHONPATH}:`pwd`"
    (build-pootle-release)$ export POOTLE_SETTINGS=~/.pootle/pootle_build.conf
    (build-pootle-release)$ make publish-pypi
    (build-pootle-release)$ deactivate
    $ unset POOTLE_SETTINGS
    $ rmvirtualenv build-pootle-release


.. _releasing#create-github-release:

Create a release on Github
--------------------------

Do the following to create the release:

#. Go to https://github.com/translate/pootle/releases/new
#. Draft a new release with the corresponding tag version
#. Convert the major changes (no more than five) in the release notes to
   Markdown with `Pandoc <http://pandoc.org/>`_. Bugfix releases can replace
   the major changes with *This is a bugfix release for the X.X.X branch.*
#. Add the converted major changes to the release description
#. Include at the bottom of the release description a link to the full release
   notes at Read The Docs
#. Attach the tarball to the release
#. Mark it as pre-release if it's a release candidate


Update Pootle website
---------------------

We use github pages for the website. First we need to checkout the pages:

.. code-block:: console

    $ git checkout gh-pages


#. In :file:`_posts/` add a new release posting. Use the same text used for the
   :ref:`Github release <releasing#create-github-release>` description,
   including the link to the full release notes.
#. Change ``$version`` as needed. See :file:`_config.yml` and
   :command:`git grep $old_release`
#. :command:`git commit` and :command:`git push` -- changes are quite quick so
   easy to review.


Announce to the world
---------------------

Let people know that there is a new version:

#. Announce on mailing lists **using plain text** emails using the same text
   (adjusting what needs to be adjusted) used for the :ref:`Github release <releasing#create-github-release>` description:

   - translate-announce@lists.sourceforge.net
   - translate-pootle@lists.sourceforge.net
   - translate-devel@lists.sourceforge.net

#. Adjust the `Pootle channel <https://gitter.im/translate/pootle>`_ notice.
   Use ``/topic [new topic]`` to change the topic. It is easier if you copy the
   previous topic and adjust it.
#. Email important users
#. Tweet about it
#. Update `Pootle's Wikipedia page <https://en.wikipedia.org/wiki/Pootle>`_


Post-Releasing Tasks
====================

These are tasks not directly related to the releasing, but that are
nevertheless completely necessary.


Bump version to N+1-alpha1
--------------------------

If this new release is a stable one, bump the version in ``master`` to
``{N+1}-alpha1``. The places to be changed are the same ones listed in
:ref:`Up version numbers <releasing#up-version-numbers>`. This prevents anyone
using ``master`` being confused with a stable release and we can easily check
if they are using ``master`` or ``stable``.


Add release notes for dev
-------------------------

After updating the release notes for the about to be released version, it is
necessary to add new release notes for the next release, tagged as ``dev``.


Other possible steps
--------------------

Some possible cleanup tasks:

- Remove your ``pootle-release`` checkout.
- Update and fix these releasing notes:

  - Make sure these releasing notes are updated on ``master``.
  - Discuss any changes that should be made or new things that could be added.
  - Add automation if you can.

- Add new sections to this document. Possible ideas are:

  - Pre-release checks
  - Change URLs to point to the correct docs: do we want to change URLs to point
    to the ``$version`` docs rather then ``latest``?
  - Building on Windows, building for other Linux distros.
  - Communicating to upstream packagers.
