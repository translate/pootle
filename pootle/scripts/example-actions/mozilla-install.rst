Mozilla L10n environment installation notes
===========================================

This should rather be handled as Fabric deployment (or puppet/chef/salt
stack?) but for now these notes should allow you to walk through this
process manually.

Mozilla build dependencies
==========================

If you want the ability to generate langpacks, you will need a Mozilla
development build environment - typically the Aurora releases are used as
that is the stage where strings are (mostly) frozen and translations can
be landed in time for beta testing.  Mozilla development build has several
additional dependencies beyond what is typically installed and/or required
for Pootle; these should be installed via ``sudo apt-get install``:

* autoconf2.13
* git
* hg
* zip

(Git and Mercurial (hg) are only needed for VCS checkout below, not for
the actual build, but leave them installed as you'll use them later on.)

The following packages ought not to be actually required, however, the
autoconf directive ``ac_add_options --disable-compile-environment`` is
currently broken (see https://bugzilla.mozilla.org/show_bug.cgi?id=862770),
so these are required whether they are actually needed or not (they also
pull in quite a lot of other packages):

* libgtk2.0-dev
* libdbus-1-dev
* libdbus-glib-1-dev
* libxt-dev
* mesa-common-dev
* yasm


Mozilla VCS checkout
====================

Two repositories are needed, ``mozilla-l10n`` from translate, and
``mozilla-aurora`` from Mozilla (the latter is only required if you want
to be able to build langpacks).  The first is checked out with git, the
second with hg (Mercurial).  Both should be checked out in the directory
configured as VCS_DIRECTORY in pootle.conf.

.. code-block:: bash

    $ export VCS_DIRECTORY=/var/www/sites/pootle/repos
    $ cd $VCS_DIRECTORY
    $ git clone https://github.com/translate/mozilla-l10n.git
    $ hg clone http://hg.mozilla.org/releases/mozilla-aurora mozilla-aurora
    
Extension actions
=================

To enable the extension actions, they need to be copied (or linked) from
pootle/scripts/example-actions/ directory to pootle/scripts/ext_actions/
directory where they will be found by Pootle.  For langpack support, the
tools/mozilla/buildxpi.py module also needs to be copied into the
pootle/scripts/ext_actions directory.

.. code-block:: bash

    $ export POOTLE_SCRIPT_DIRECTORY=/var/www/sites/pootle/src/pootle/scripts
    $ cd $POOTLE_SCRIPT_DIRECTORY
    $ ln example-actions/moz*.py ext_actions/
    $ cp ~/env/src/translate-toolkit/tools/mozilla/buildxpi.py ext_actions/
    # you may also find buildxpi.py in ~/env/bin/
