.. _initial-data-and-upgrade:

Initial data and upgrade
========================

When developing is not uncommon to have to alter the database schema (adding,
changing or removing fields to models), provide new initial data on fresh
installations or alter the data on the database when upgrading.

The following guidelines are meant to make clear where to put the code:

- When altering the database schema, add a migration.
- When adding new initial data, add the code to ``pootle.core.initdb``.
- When altering the data on the database on upgrading, add the code to
  ``pootle.apps.pootle_misc.upgrade.pootle``.

  .. note:: If this upgrade code is going to be used for providing initial data
     as well, then it must be placed instead on ``pootle.core.initdb`` and
     referenced from ``pootle.apps.pootle_misc.upgrade.pootle``.
