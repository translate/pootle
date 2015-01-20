.. _release-process:

Release Process
===============

This document describes the release process Pootle follows starting from
version 2.5.

.. _release-process_principles:

Principles
----------

- *Align Pootle releases with Django releases*, keeping compatibility with the
  latest version of the framework and avoiding the use, and maintenance
  headache, of deprecated code.
- *Time-based feature releases every six months*, this ensures that users, who
  don't want to run from *master*, and packagers have regular features updates.
- *Master is always stable*, this ensures that anyone can run a production
  server from *master*.  It also reduces our effort of maintaining multiple
  branches in development.  Lastly, it helps create a discipline of landing
  stable features.


Rules
-----

The principles above extended into these rules.

#. Feature releases are made every six months.
#. Feature releases (as distinct from a bug fix release) are only against the
   latest Django version that Pootle supports i.e. we won't backport features.
#. Security fixes are made to the last two time-based releases.
#. Older time-based releases are no longer supported.
#. Pootle should run on Django N and N-1.
#. *master* is always releasable.
#. All schema related and major changes are made in feature branches.
#. One month before a time-based release, when *master* is in a stabilising
   period, schema and feature changes should not landed on *master*.


Version Numbering
-----------------

A Pootle version number consists of ``Major-Minor-Point-Bugfix`` as in
``2.5.0`` or ``2.6.1.2``

Pootle's minor number is changed to indicate the latest version of Django that
is supported.  Thus when the latest version of Django is released, and Pootle
gains support for this version, then the Pootle minor number will change.

.. note:: Pootle 2.5.0 is an exception to this rule.  It did not support
   Django 1.5 at the time of release.

Every six months, when a new release train is ready to be shipped, Pootle's
point version will be incremented.

Any critical security fixes will automatically result in a new bugfix release.


Examples
--------

Understanding the number and release train with some examples:

*Django 1.5* is the latest version of Django:

- Pootle is named ``2.5`` and should support *Django 1.5*.
- Pootle ``2.5.0`` is released as the first time-based release.
- Next time-based release would be ``2.5.1``.

A security issue is detected in Pootle ``2.5.0``

- The first security release ``2.5.0.1`` is made
- Next time-based release is still ``2.5.1``

*Django 1.6* is released:

- Current Pootle release is ``2.5.4``, next Pootle release will be ``2.6.0``
- When ``2.6.0`` is out we will support Pootle ``2.6.0`` and ``2.5.4``, all
  previous versions will be unsupported.

A security issue is discovered which impacts all our supported time-based
releases:

- We release ``2.6.0.1`` and ``2.5.4.1``

Time-based release ``2.6.1`` is released six months after ``2.6.0``

- We now support ``2.6.1`` and ``2.6.0``
- Support is dropped for ``2.5.4`` which is now a year old.


The Release Train: Point Releases Every Six Months
--------------------------------------------------

Within the priciple that *master* is always deployable we aim to ensure a
period of stability to allow easier release in the month prior to a time-based
release.

First-Fifth month
  All major work and features are allowed, strings may be broken.

Sixth month
  Feature work that doesn't change the DB schema, bug fixes, refinements and
  translations. Strings are frozen.

If for some reason there's feature work that changes the schema during month
six of the release train, the feature will go in its own branch and won't be
merged until the next release train starts.

Security fixes are applied anytime in the release train.


Branching Strategy
------------------

The next Pootle version is always baked in the *master* branch. Exceptions are
security fixes which are committed in *master* and cherry-picked to the
currently supported time-based release branches.

A new time-based release is made off of *master*, incrementing the point
version.  Every time a new release happens, a new branch is created. These
branches are named after their version numbers: if *master* is to become
version ``2.6.2``, then the new branch will be named *stable/2.6.2*. The actual
release is also tagged, in this case as *2.6.2*.

Security fixes are made on the relevant release branches.  So the first
security release on *stable/2.6.2* would be tagged as *2.6.2.1*.

Features that produce schema changes or are quite invasive go into feature
branches named *feature/<feature-name>*. Once the feature is ready to be
integrated within the first phase of the release train, they're merged into
*master*.
