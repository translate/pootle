=======================
Making a Pootle Release
=======================

These instructions are the guidelines for anyone making a Pootle commit.

Summary
=======
#. git clone git@github.com:translate/pootle.git pootle-release
#. Create release notes
#. Adjust the roadmap
#. Up version number
#. Update translations
#. make build
#. Test install and other tests
#. Tag the release
#. Publish on PyPI
#. Upload to Sourceforge
#. Add product version to Bugzilla
#. Release documentation
#. Update translate website
#. Update Pootle dashboard
#. Unstage sourceforge
#. Announce to the world
#. Cleanup

Other possible steps
--------------------
We need to check and document these if needed:

- Pre-release checks
- Build docs: we need to check if we need to build the docs for the release
  tarball.
- Change URLs to point to the correct docs: do we want to change URLs to point
  to the $version docs rather then 'latest'?
- Building on Windows, building for other Linux distros. We have produced 
- Communicating to upstream packagers


Pre-release instructions
========================

Upload and announce translations
--------------------------------
We need to give localizers enough time to localize Pootle.  They need time to
do the actual translation and to feedback on any errors that they might
encounter.

To make a new template::

   make pot

And upload the templates to Pootle for translation. Update current translations
against templates either on Pootle or in code and commits these updated files
to Git.

Announce the new translations using these two channels:

1. The News tab on Pootle -- for those not on any mailing list
2. The translate-pootle and translate-devel mailing lists -- for those who might
   miss the news.


String freeze
-------------
We want to give a string freeze at least 2-4 weeks before a release.  Announce
that on the mailing lists.

If we do have a string freeze break then announce those to people.

A string freeze would normally run between an RC1 and a released version.


Double check version dependencies
---------------------------------
Make sure the versions listed in docs/server/installation.rst match those in
requirements/base.txt


Detailed release instructions
=============================

Get a clean checkout and new virtualenv
---------------------------------------
We work from a clean checkout to ensure that everything you are adding to the
build is what is in VC and doesn't contain any of your uncommitted changes.  It
also ensure that someone else could replicate your process. ::

    git clone git@github.com:translate/pootle.git pootle-release
    cd pootle-release
    git submodule update --init
    mkvirtualenv pootle-release
    pip install -r requirements/build.txt

Create release notes
--------------------
The release notes will be used in these places:

- Pootle website -- `download page
  <http://pootle.translatehouse.org/download.html>`_ (used in gh-pages)
- Sourceforge download -- README.rst (used to give user info)
- Email announcements -- text version

We create our release notes in reStructured Text, since we use that elsewhere
and since it can be rendered well in some of our key sites.

First we need to create a log of changes in Pootle, which is done generically
like this::

    git log $version-1..HEAD > docs/release/$version.rst

Or a more specific example::

    git log 2.5.0..HEAD > docs/releases/2.5.1.rst

Edit this new file.  You can use the commits as a guide to build up the release
notes.  You should remove all log messages before the release.

.. note:: Since the release notes will be used in places that allow linking we
   use links within the notes.  These should link back to products websites
   (`Virtaal <http://virtaal.org>`_, `Pootle
   <http://pootle.translatehouse.org>`_, etc), references to `Translate
   <http://translatehouse.org>`_ and possibly bug numbers, etc.

Read for grammar and spelling errors.

.. note:: When writing the notes please remember:

   #. The voice is active. 'Translate has released a new version of the
      toolkit', not 'A new version of the toolkit was released by Translate'.
   #. The connection to the users is human not distant.
   #. We speak in familiar terms e.g. "I know you've been waiting for this
      release" instead of formal.

We create a list of contributors using this command::

   git log 2.5.0..HEAD --format='%aN, ' | awk '{arr[$0]++} END{for (i in arr){print arr[i], i;}}' | sort -rn | cut -d\  -f2-


Adjust the roadmap
------------------
The roadmap file needs to be updated.  Remove things that are part of this
release.  Adjust any version numbering if for example we're moving to Django
1.6 we need to change the proposed release numbers.

Look at the actual roamap commitments and change if needed.  These will remain
during the lifetime of this version so it is good to adjust them before we
branch.


Up version numbers
------------------
Update the version number in:

- ``pootle/__version__.py``
- ``docs/conf.py``

In ``__version__.py``, bump the build number if anybody used the toolkit with
the previous number, and there have been any changes to code touching stats or
quality checks.  An increased build number will force a toolkit user, like
Pootle, to regenerate the stats and checks.

.. FIXME I don't think the above about build number is correct for Pootle

For ``conf.py`` change ``version`` and ``release``

.. note:: FIXME -- We might want to automate the version and release info so
   that we can update it in one place.

The version string should follow the pattern::

    $MAJOR-$MINOR-$MICRO[-$EXTRA]

E.g. ::

    1.10.0
    0.9.1-rc1 

``$EXTRA`` is optional but all the three others are required.  The first
release of a ``$MINOR`` version will always have a ``$MICRO`` of ``.0``. So
``1.10.0`` and never just ``1.10``.


Check copyright dates
---------------------

Update any copyright dates in ``docs/conf.py:copright`` and anywhere else that
needs fixing.::

    $ git grep 2013  # Should pick up anything that should be examined


Update requirements versions
----------------------------
Update the minimum version number for the requirements in:

- ``requirements/``
- ``pootle/depcheck.py``


Update the requirements files::

    make requirements-pinned.txt

.. note:: This creates the following files:

       - requirements-pinned.txt - the maximum available version when we
         released.  Chances are we've tested with these and they are good.
         Using this would prevent a person from intalling something newer but
         untested.

.. FIXME check that these are actually packaged next time we build as they are
   files for release.


Update translations
-------------------
Update the translations from the `Pootle server
<http://pootle.locamotion.org/projects/pootle>`_

#. Download all translations::

       $ make get-translations

#. Update ``pootle/locale/LINGUAS`` to list the languages we would like to
   ship. While we package all PO files, this is an indication of which ones we
   want packagers to use.  The requirement is roughly 80% translated with no
   obvious variable errors. Languages with a small userbase can be included. ::

       $ make linguas

   Check the output and make any adjustments such as adding back languages that
   don't quite make the target but you wish to ship.

#. Build translations to check for errors:

   .. code-block:: bash

       $ make mo # Build all LINGUAS enabled languages


Build the package
-----------------
Building is the first step to testing that things work.  From your clean
checkout run::

    make mo-all # if we are shipping an pre-release
    make build


This will create a tarball in ``dist/`` which you can use for further testing.

.. note:: We use a clean checkout just to make sure that no inadvertant changes
   make it into the release.


Test install and other tests
----------------------------
The easiest way to test is in a virtualenv.  You can install the new toolkit
using::

    mkvirtualenv pootle-testing
    pip install path/to/dist/Pootle-$version.tar.bz2

This will allow you test installation of the software.

You can then proceed with other tests such as checking:

#. Quick installation check::

      pootle init
      pootle setup
      pootle start
      # browse to localhost:8000

#. Documentation is available
#. Installation documention is correct

   - Follow the :doc:`installation </server/installation>` and :doc:`hacking
     <hacking>` guides to ensure that they are correct.

#. Meta information about the package is correct. See pypi section of reviewing
   meta data.

To cleanup::

    deactivate
    rmvirtualenv pootle-testing


Tag the release
---------------
You should only tag once you are happy with your release as there are some
things that we can't undo. ::

    git tag -a 2.5.0 -m "Tag version 2.5.0"
    git push --tags

If this is the final release then there should be a stable branch e.g.
``stable/2.5.0``, so create one if it does not already exist.


Publish on PyPI
---------------
Publish the package on the `Python Package Index
<https://pypi.python.org/pypi>`_ (PyPI)

- `Submitting Packages to the Package Index
  <http://wiki.python.org/moin/CheeseShopTutorial#Submitting_Packages_to_the_Package_Index>`_

.. note:: You need a username and password on https://pypi.python.org and have
   rights to the project before you can proceed with this step.

   These can be stored in ``$HOME/.pypirc`` and will contain your username and
   password. A first run of ``./setup.py register`` will create such a file.
   It will also actually publish the meta-data so only do it when you are
   actually ready.

Review the meta data. This is stored in ``setup.py``, use ``./setup.py --help``
to se some options to display meta-data. The actual long description is taken
from ``/README.rst``.

To test before publishing run::

    make test-publish-pypi

Then to actually publish::

    make publish-pypi


Copy files to sourceforge
-------------------------
Publishing files to the Translate Sourceforge project.

.. note:: You need to have release permissions on sourceforge to perform this
   step.

- http://sourceforge.net/projects/translate/files/Pootle/

You will need:

- Tarball of the release
- Release notes in reStructured Text

#. Create a new folder in the `Pootle Sourceforge release folder
   <https://sourceforge.net/projects/translate/files/Pootle/>`_ using the 'Add
   Folder' button.  The folder name must be the same as the release name e.g.
   ``2.5.0-rc1``.  Mark this as being for staging for the moment.
#. ``make publish-sourceforge`` will give you the command to upload your
   tarball and ``README.rst``.

   #. Upload tarball for release.
   #. Upload release notes as ``README.rst``.
   #. Click on the info icon for ``README.rst`` and tick "Exclude Stats" to
      exlude the README from stats counting.

#. Check ``README.rst``. Since this is generated on Sourceforge, without
   reference to the docs folder, some of the links will be broken.

   #. Check all links
   #. If broken links exist then download ``README.rst`` from Sourceforge, make
      changes and upload your adjusted version.  Don't change the version in
      ``releases/`` as we want that to continue to work correctly.

#. Final checks:

   #. Check that the README.rst for the parent ``Pootle`` folder is still
      appropriate, this text is the text from ``/README.rst``.
   #. Check all the links in ``README.rst`` files for existing releases, new
      release and the parent folders.


Add product version to Bugzilla
-------------------------------
We need to allow users to report issues against the released version.

#. In Administration->Products add a product version.
#. Review existing versions that are available and disable older version from
   accepting bug reports.


Release documentation
---------------------
We need a tagged release or branch before we can do this.  The docs are
published on Read The Docs.

- https://readthedocs.org/dashboard/pootle/versions/

Use the admin pages to flag a version that should be published.  When we have
branched the stable release we use the branch rather then the tag i.e.
``stable/2.5.0`` rather than ``2.5.0`` as that allows any fixes of
documentation for the ``2.5.0`` release to be immediately available.

Change all references to docs in the Pootle code to point to the branched
version as apposed to the latest version.

.. FIXME we should do this with a config variable to be honest!

Update Pootle website
---------------------
We use github pages for the website. First we need to checkout the pages::

    git checkout gh-pages

#. In ``_posts/`` add a new release posting.  This is in Markdown format (for
   now), so we need to change the release notes .rst to .md, which mostly means
   changing URL links from '```xxx <link>`_``' to ``[xxx](link)``.
#. Change $version as needed. See ``download.html``, ``_config.yml`` and
   ``git grep $old_release``
#. ``git commit`` and ``git push`` -- changes are quite quick so easy to
   review.

.. note:: FIXME it would be great if gh-pages accepted .rst, maybe it can if we
   prerender just that page?


Update Pootle dashboard
-----------------------
The dashboard used in Pootle's dashboard is updated in its own project:

#. git clone git@github.com:translate/pootle-dashboard.git
#. Edit index.html to contain the latest release info
#. Add the same info in alerts.xml pointing to the release in RTD
   ``release/$version.html``

Do a ``git pull`` on the server to get the latest changes from the repo.


Unstage on sourceforge
----------------------
If you have created a staged release folder, then unstage it now.


Announce to the world
---------------------
Let people know that there is a new version:

#. Announce on mailing lists:
   Send the announcement to the translate-announce mailing lists on
   translate-announce@lists.sourceforge.net
   translate-pootle@lists.sourceforge.net
#. Adjust the #pootle channel notice. Use ``/topic`` to change the topic.
#. Email important users
#. Tweet about it


Cleanup
-------
Some possible cleanup tasks:

- Remove any RC builds from the sourceforge download pages and add redirects to
  Sourceforge ``Pootle`` top level download page.
- Checkin any release notes and such (or maybe do that before tagging).
- Remove your pootle-release checkout.
- Remove pootle-release virtualenv: ``deactivate; rmvirtualenv pootle-release``
- Update and change things based on what you learnt, don't wait:

  - Update and fix these release notes and make sure they are on ``master``.
  - Dicuss any changes that should be made or new things that could be added
  - Add automation if you can
