Making a Pootle Release
***********************

This page is divided in four sections. The first one lists the tasks that must
be performed before creating a package. The second section includes a list of
tasks  to get a valid package. The third one to get the package published and
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

   .. code-block:: bash

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

.. code-block:: bash

    $ git clone git@github.com:translate/pootle.git pootle-release
    $ cd pootle-release
    $ git submodule update --init


Double check version dependencies
---------------------------------

Make sure the versions listed in :file:`docs/server/installation.rst` match
those in :file:`requirements/base.txt`.


Update requirements versions
----------------------------

Update the minimum version number for the requirements in:

- :file:`requirements/`
- :file:`pootle/depcheck.py`


Update the requirements files:

.. code-block:: bash

    $ make requirements-pinned.txt


.. note:: This creates the following files:

       - :file:`requirements-pinned.txt` - the maximum available version when
         we released.  Chances are we've tested with these and they are good.
         Using this would prevent a person from intalling something newer but
         untested.

.. FIXME check that these are actually packaged next time we build as they are
   files for release.


Adjust the roadmap
------------------

The roadmap file needs to be updated.  Remove things that are part of this
release.  Adjust any version numbering if for example we're moving to Django
1.6 we need to change the proposed release numbers.

Look at the actual roadmap commitments and change if needed. These will remain
during the lifetime of this version so it is good to adjust them before we
branch.


Check copyright dates
---------------------

Update any copyright dates in :file:`docs/conf.py:copyright` and anywhere else
that needs fixing.

.. code-block:: bash

    $ git grep 2013  # Should pick up anything that should be examined


Update translations
-------------------

Update the translations from the `Pootle server
<http://pootle.locamotion.org/projects/pootle>`_

#. Download all translations

   .. code-block:: bash

       $ make get-translations

#. Update :file:`pootle/locale/LINGUAS` to list the languages we would like to
   ship. While we package all PO files, this is an indication of which ones we
   want packagers to use.  The requirement is roughly 80% translated with no
   obvious variable errors. Languages with a small userbase can be included.

   .. code-block:: bash

       $ make linguas

   Check the output and make any adjustments such as adding back languages that
   don't quite make the target but you wish to ship.

#. Build translations to check for errors:

   .. code-block:: bash

       $ make mo  # Build all LINGUAS enabled languages


Create release notes
--------------------

The release notes will be used in these places:

- Pootle website -- `download page
  <http://pootle.translatehouse.org/download.html>`_ (used in gh-pages)
- Email announcements -- text version

We create our release notes in reStructured Text, since we use that elsewhere
and since it can be rendered well in some of our key sites.

First we need to create a log of changes in Pootle, which is done generically
like this:

.. code-block:: bash

    $ git log $previous_version..HEAD > docs/release/$version.rst


Or a more specific example:

.. code-block:: bash

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

.. code-block:: bash

    $ git log 2.5.0..HEAD --format='%aN, ' | awk '{arr[$0]++} END{for (i in arr){print arr[i], i;}}' | sort -rn | cut -d\  -f2-


Up version numbers
------------------

Update the version number in:

- :file:`pootle/__version__.py`
- :file:`docs/conf.py`

In :file:`pootle/__version__.py`, bump the build number if anybody used Pootle
with the previous number, and there have been any changes to code touching
stats or quality checks.

For :file:`docs/conf.py` change ``version`` and ``release``.

.. note:: FIXME -- We might want to automate the version and release info so
   that we can update it in one place.


The version string should follow the pattern::

    $MAJOR-$MINOR-$MICRO[-$EXTRA]

E.g. ::

    1.10.0
    0.9.1-rc1

``$EXTRA`` is optional but all the three others are required.  The first
release of a ``$MINOR`` version will always have a ``$MICRO`` of ``.0``. So
``2.6.0`` and never just ``2.6``.


Build the package
-----------------

Building is the first step to testing that things work. From your clean
checkout run:

.. code-block:: bash

    $ mkvirtualenv build-pootle-release
    (build-pootle-release)$ pip install -r requirements/build.txt
    (build-pootle-release)$ make mo-all  # If we are shipping an RC
    (build-pootle-release)$ make build
    (build-pootle-release)$ deactivate
    $ rmvirtualenv build-pootle-release


This will create a tarball in :file:`dist/` which you can use for further
testing.

.. note:: We use a clean checkout just to make sure that no inadvertant changes
   make it into the release.


Test install and other tests
----------------------------

The easiest way to test is in a virtualenv. You can test the installation of
the new Pootle using:

.. code-block:: bash

    $ mkvirtualenv test-pootle-release
    (test-pootle-release)$ pip install $path_to_dist/Pootle-$version.tar.bz2


You can then proceed with other tests such as checking:

#. Quick installation check:

   .. code-block:: bash

     (test-pootle-release)$ pootle init
     (test-pootle-release)$ pootle setup
     (test-pootle-release)$ pootle start
     (test-pootle-release)$  # Browse to localhost:8000
     (test-pootle-release)$ deactivate
     $ rmvirtualenv test-pootle-release

#. Documentation is available in the package
#. Installation documentation is correct

   - Follow the :doc:`installation </server/installation>` and :doc:`hacking
     <hacking>` guides to ensure that they are correct.

#. Meta information about the package is correct. This is stored in
   :file:`setup.py`, to see some options to display meta-data use:

   .. code-block:: bash

     $ ./setup.py --help

   Now you can try some options like:

   .. code-block:: bash

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


Publish the new release
=======================

Once we have a valid package it is necessary to publish it and announce the
release.


Tag and branch the release
--------------------------

You should only tag once you are happy with your release as there are some
things that we can't undo. You can safely branch for a ``stable/`` branch
before you tag.

.. code-block:: bash

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


Publish on PyPI
---------------

.. - `Submitting Packages to the Package Index
  <http://wiki.python.org/moin/CheeseShopTutorial#Submitting_Packages_to_the_Package_Index>`_


.. note:: You need a username and password on `Python Package Index (PyPI)
   <https://pypi.python.org>`_ and have rights to the project before you can
   proceed with this step.

   These can be stored in :file:`$HOME/.pypirc` and will contain your username
   and password. A first run of:

   .. code-block:: bash

       $ ./setup.py register

   will create such file. It will also actually publish the meta-data so only
   do it when you are actually ready.


Run the following to publish the package on PyPI:

.. code-block:: bash

    $ make publish-pypi


Create a release on Github
--------------------------

- https://github.com/translate/pootle/releases/new

You will need:

- Tarball of the release
- Release notes in Markdown


Do the following to create the release:

#. Draft a new release with the corresponding tag version
#. Convert the major changes in the release notes to Markdown with `Pandoc
   <http://johnmacfarlane.net/pandoc/>`_ and add those to the release
#. Include a link to the full release notes in the description
#. Attach the tarball to the release
#. Mark it as pre-release if it's a release candidate.


Update Pootle website
---------------------

We use github pages for the website. First we need to checkout the pages:

.. code-block:: bash

    $ git checkout gh-pages


#. In :file:`_posts/` add a new release posting.  This is in Markdown format
   (for now), so we need to change the release notes .rst to .md, which mostly
   means changing URL links from ```xxx <link>`_`` to ``[xxx](link)``.
#. Change ``$version`` as needed. See :file:`download.html`,
   :file:`_config.yml` and :command:`git grep $old_release`
#. :command:`git commit` and :command:`git push` -- changes are quite quick so
   easy to review.

.. note:: FIXME it would be great if gh-pages accepted .rst, maybe it can if we
   prerender just that page?


Update Pootle dashboard
-----------------------

.. note:: Do not do this for release candidates, only for final releases.

The dashboard used in Pootle's dashboard is updated in its own project:

#. :command:`git clone git@github.com:translate/pootle-dashboard.git`
#. Edit :file:`index.html` to contain the latest release info
#. Add the same info in :file:`alerts.xml` pointing to the release in RTD
   :file:`release/$version.html`

Do a :command:`git pull` on the server to get the latest changes from the repo.


Announce to the world
---------------------

Let people know that there is a new version:

#. Announce on mailing lists:

   - translate-announce@lists.sourceforge.net
   - translate-pootle@lists.sourceforge.net

#. Adjust the #pootle channel notice. Use ``/topic`` to change the topic.
#. Email important users
#. Tweet about it
#. Update `Pootle's Wikipedia page <http://en.wikipedia.org/wiki/Pootle>`_


Post-Releasing Tasks
====================

These are tasks not directly related to the releasing, but that are
nevertheless completely necessary.


Bump version to N+1-alpha1
--------------------------

If this new release is a stable one bump the version in ``master`` to
``{N+1}-alpha1``. This prevents anyone using ``master`` being confused with a
stable release and we can easily check if they are using ``master`` or
``stable``.


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
