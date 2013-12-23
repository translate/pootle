.. _evernote-changelog:

Evernote Changelog
==================

This page documents the major changes done for each production release.
For the smaller details and bug fixes, check the repository's logs and
history, including the comparison view to the previous release.

Release .next
-------------

- `Commit comparison wrt previous release
  <https://github.com/evernote/pootle/compare/release-current...HEAD>`_


Release `2013-12-19`_
---------------------

- New navigation scheme.

  + All directories/files for a project are displayed in a new drop-down.
    The differences between directories and files are visually
    highlighted. (`#74`_)

  + Directories/files can be navigated and translated across multiple
    languages in a project. (`#75`_)

  + Tabs have been replaced in favor of drop-down menus. (`#76`_)

  + The editor search box is now displayed in the action links section,
    keeping its positioning consistent with the overview page. (`#83`_)

  + A new action link in the editor, *Go back to overview*, allows users
    to go back to the same place they entered translation mode from.
    (`#77`_)

- Upgraded jQuery to 2.x and applied a bunch of fixes to the Tipsy plugin,
  avoiding ad-hoc hacks to remove dangling tips. (`#25`_, `#63`_)

- Custom word counting calculation method. (`e7f5684d20`_, `7cbc6b5398`_,
  `a44a12556d`_, `400d20e191`_, `e92f4ca4fd`_,)

- Muted checks are now displayed and can be unmuted. Apart from that, when
  a users mutes or unmutes a quality check, the action will be recorded in
  the unit's timeline. (`#54`_, `#56`_)

- Major speed improvements when calculating last action information.
  (`79c7e06f50`_, `81d40ffed2`_)

- Individual quality checks can now be recalculated via the ``--check``
  flag passed to the ``refresh_stats`` management command. (`fd70c41ce8`_)

- When going through all units in the translation editor, users will be
  automatically redirected back to overview. (`#87`_)

- `Commit comparison wrt previous release
  <https://github.com/evernote/pootle/compare/release-2013-11-29...release-2013-12-19>`_

.. _2013-12-19: https://github.com/evernote/pootle/releases/tag/release-2013-12-19
.. _#74: https://github.com/evernote/pootle/issues/74
.. _#75: https://github.com/evernote/pootle/issues/75
.. _#76: https://github.com/evernote/pootle/issues/76
.. _#83: https://github.com/evernote/pootle/issues/83
.. _#77: https://github.com/evernote/pootle/issues/77
.. _e7f5684d20: https://github.com/evernote/pootle/commit/e7f5684d20
.. _7cbc6b5398: https://github.com/evernote/pootle/commit/7cbc6b5398
.. _a44a12556d: https://github.com/evernote/pootle/commit/a44a12556d
.. _400d20e191: https://github.com/evernote/pootle/commit/400d20e191
.. _e92f4ca4fd: https://github.com/evernote/pootle/commit/e92f4ca4fd
.. _#25: https://github.com/evernote/pootle/issues/25
.. _#63: https://github.com/evernote/pootle/issues/63
.. _#54: https://github.com/evernote/pootle/issues/54
.. _#56: https://github.com/evernote/pootle/issues/56
.. _79c7e06f50: https://github.com/evernote/pootle/commit/79c7e06f50
.. _81d40ffed2: https://github.com/evernote/pootle/commit/81d40ffed2
.. _fd70c41ce8: https://github.com/evernote/pootle/commit/fd70c41ce8
.. _#87: https://github.com/evernote/pootle/issues/87


Release `2013-11-29`_
---------------------

- Bugfix release.

- `Commit comparison wrt previous release
  <https://github.com/evernote/pootle/compare/release-2013-11-28...release-2013-11-29>`_

.. _2013-11-29: https://github.com/evernote/pootle/releases/tag/release-2013-11-29


Release `2013-11-28`_
---------------------

- Implemented project notifications by reusing static pages. Notifications
  are per-project and are displayed across languages (automatically
  adapting any hyperlinks). The implementation can be considered as a
  work-around/hack. (`#59`_)

- Added ``--calculate-checks`` parameter to the ``refresh_stats`` command.
  (`6ab0c05e0a`_)

- Overview pages now report the last time a unit was added to a
  store/project. In the browsing tables a *Last Updated* column is
  displayed and in the extended stats *Created* and *Last Updated*
  dates. (`#61`_)

- If the currently-submitted unit has pending checks, the editor won't
  advance to the next unit and it will be updated displaying the
  unresolved checks. (`#53`_)

- When there are failing checks, overview tables now display the number of
  units which have failing checks, not the total number of failing checks.
  (`#66`_)

- The *Submit*/*Suggest* button is disabled until a change over the
  initial state of the unit is detected. (`#67`_)

- `Commit comparison wrt previous release
  <https://github.com/evernote/pootle/compare/release-2013-11-15...release-2013-11-28>`_

.. _2013-11-28: https://github.com/evernote/pootle/releases/tag/release-2013-11-28
.. _#59: https://github.com/evernote/pootle/issues/59
.. _6ab0c05e0a: https://github.com/evernote/pootle/commit/6ab0c05e0a
.. _#61: https://github.com/evernote/pootle/issues/61
.. _#53: https://github.com/evernote/pootle/issues/53
.. _#66: https://github.com/evernote/pootle/issues/66
.. _#67: https://github.com/evernote/pootle/issues/67


Release `2013-11-15`_
---------------------

- Added maintenance mode via middleware. (`#39`_)

- Removed the concept of *pages* in the editor and its underlying APIs.
  This was problematic and buggy. (`#48`_)

- Table sorting is now remembered across overview pages, and not
  separately in project, language and translation project pages. (`#47`_)

- `Commit comparison wrt previous release
  <https://github.com/evernote/pootle/compare/release-2013-11-08...release-2013-11-15>`_

.. _2013-11-15: https://github.com/evernote/pootle/releases/tag/release-2013-11-15
.. _#39: https://github.com/evernote/pootle/issues/39
.. _#48: https://github.com/evernote/pootle/issues/48
.. _#47: https://github.com/evernote/pootle/issues/47


Release `2013-11-08`_
---------------------

- Incorporated ``refresh_all_stats`` functionality into ``refresh_stats``.
  (`f1bb127e3f`_)

- Fixed and avoided any inconsistencies in the unit's submitter
  information. (`#33`_)

- `Commit comparison wrt previous release
  <https://github.com/evernote/pootle/compare/release-2013-10-29...release-2013-11-08>`_

.. _2013-11-08: https://github.com/evernote/pootle/releases/tag/release-2013-11-08
.. _#33: https://github.com/evernote/pootle/issues/33
.. _f1bb127e3f: https://github.com/evernote/pootle/commit/f1bb127e3f


Release `2013-10-29`_
---------------------

- Major rewrite of the way statistics are handled.
  On the backend side, numbers are now calculated separately and cache
  invalidation is not as aggressive as before. Models can inherit from a
  ``TreeItem`` mixin class in order to gain the caching mechanisms. The
  ``refresh_all_stats`` command has been added to use faster calculations
  methods too.
  On the frontend side, stats are now loaded asynchronously, thus any
  pending calculations no longer block page loads. (`#12_`)

- Command and action logging. (`fdaf702e0`_, `d8d70bfc`_)

- Rewritten contact form. Allows both to contact site owners from any page
  as well as to report any issues with strings. (`#15`_)

- Implemented export view for cross-language and cross-project views.
  (`#9`_)

- The editor now displays the numbering for units, not pages. (`BZ 2215`_)

- Implemented new header styling.

- `Commit comparison wrt previous release
  <https://github.com/evernote/pootle/compare/release-2013-08-27...release-2013-10-29>`_

.. _2013-10-29: https://github.com/evernote/pootle/releases/tag/release-2013-10-29
.. _#12: https://github.com/evernote/pootle/issues/12
.. _fdaf702e0: https://github.com/evernote/pootle/commit/fdaf702e0
.. _d8d70bfc: https://github.com/evernote/pootle/commit/d8d70bfc
.. _#15: https://github.com/evernote/pootle/issues/15
.. _#9: https://github.com/evernote/pootle/issues/9
.. _BZ 2215: http://bugs.locamotion.org/show_bug.cgi?id=2215


Release `2013-08-27`_
---------------------

- `Forked upstream project`_.

- Major cleanups and removed unused features. For more details check the
  `<upstream-differences>`_ document.

- Implemented global search. This allows to perform searches and edit
  units in collections that span multiple projects across languages,
  multiple languages across projects, or even the whole server.
  (`BZ 2719`_)

- Added screenshot prefix URL for projects, which allow integrating
  screenshots for units. The images are retrieved from public Evernote
  notebooks. (`a0747fcfc4`_)

- Added system user that represents batch actions done via any management
  commands. (`cbd26d8b`_)

.. _2013-08-27: https://github.com/evernote/pootle/releases/tag/release-2013-08-27
.. _Forked upstream project: https://github.com/evernote/pootle/commit/8140ff1706
.. _BZ 2719: http://bugs.locamotion.org/show_bug.cgi?id=2719
.. _a0747fcfc4: https://github.com/evernote/pootle/commit/a0747fcfc4
.. _cbd26d8b: https://github.com/evernote/pootle/commit/cbd26d8b
