.. _release-process:

Release process
===============

This document describes the release process Pootle will follow starting from
version 2.5.

The main idea is to align Pootle releases with Django releases, keeping
compatibility with the latest version of the framework and avoiding the use of
deprecated code that no longer works.

Since that period of time can go from 6 up to 9 months resulting in quite long
leveraging periods, there will be scheduled releases every three months.


The release train: point releases every three months
----------------------------------------------------

There will be a three-month release train where change types will be split upon
time.

First month
  Any big feature work will go within the first month. Schema changes will only
  be permitted during this period.

Second month
  Feature work that doesn't change the DB schema and bug fixes.

Third month
  Bug fixes, refinements and translations.


If for some reason there's feature work that changes the schema during months
2-3 of the release train, the feature will go in its own branch and won't be
merged until the next release train starts.

Security fixes are applied anytime in the release train.


Version numbering
-----------------

Whenever a minor version of Django is released, Pootle's minor version will be
changed to match the latest supported Django version.

Every three months when a new release train is ready to be shipped, Pootle's
point version will be incremented.

Any critical security fixes will automatically result in a new point release.

Take the following timeline as an example:

- Django 1.5 released → Pootle 2.5 released

- 3-month baking period → Pootle 2.5.1 released

- Critical security bug → Pootle 2.5.2 released

- 3-month baking period → Pootle 2.5.3 released

- Django 1.6 released → Pootle 2.6 released

If in the above-mentioned example Django 1.6 is delayed, there could be a
Pootle 2.5.4 release that reflects the latest 3-month baking period. Django 1.6
could even be released before the 3-month baking period is over — in that
situation the release would slip a little bit.


Branching strategy
------------------

The next version is always baked in the *master* branch. Exceptions are
security fixes which are committed in *master* and cherry-picked to the latest
release branch. A new release is made off the latest release, incrementing the
point version.

Every time a new release happens, a new branch is created with the respective
code. These branches are named after their version numbers: if *master* will
become version 2.6.2, the new branch will be named *2.6.2*.

Features that produce schema changes will go into feature branches named like
*feature/<feature-name>*. Once they're ready to be integrated within the first
phase of the release train, they're merged into *master*.
