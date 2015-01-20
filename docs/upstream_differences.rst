.. _upstream-differences:

Changes With Respect To Upstream
================================

Evernote's needs differ from the Pootle-as-a-product perspective, and we
have seen the need to `fork the upstream product
<https://github.com/evernote/pootle/commit/8140ff1706>`_ to adapt it to
our specific needs. This involves adding new features and customizing the
existing product. We have also ripped out unneeded stuff and cleaned up
code to make it easier for us to work with no distractions.


Feature Differences
-------------------

Added Features
^^^^^^^^^^^^^^

- New management commands: ``revision``, ``changed_languages``,
  ``test_checks``, ``refresh_scores``.

- User scores and rating based on submission similarities.

- Whole new set of quality checks (plus the related ``test_checks``
  management command).

- Screenshot prefix URL to allow integrating screenshots for units.

- Evernote-specific apps: reports.

- Landing page for anonymous users.

- Ability to list top scorers over a period of time.

- ElasticSearch-based local TM.


Changed Features
^^^^^^^^^^^^^^^^

- Custom user model.

- Richer and more responsive statistics. *Last Updated* dates for stores
  and projects are tracked, for instance. These statistics are also
  available for the *All Projects* view.

- ``refresh_stats`` has been refined to be faster, and allows extra
  options.

- Quality checks. A custom set of quality checks has been incorporated.

- Authentication is handled via Evernote (*evernote_auth* app).

- Word count function can be customized in the settings, and a new method
  has been incorporated (omits placeholders and words that shouldn't be
  translated). Non-empty units with 0 words are immediately translated and
  marked as fuzzy.

- Adjusted ``update_translation_projects`` behavior not to delete
  directories from the filesystem.

- Changed the way we determine which units need to be sync'ed to disk.


Removed Features
^^^^^^^^^^^^^^^^

- SQLite support.

- LDAP support.

- Monolingual file format support.

- Support for Version Control Systems.

- News, notifications and RSS feeds.

- Lookup backends.

- Offline translation, file uploads.

- Update against templates. (Basically templates aren't needed)

- User registration. *django-registration* has been removed and new users
  need to use their Evernote accounts.

- Public API.

- Project/Language/Translation Project descriptions.

- Hooks.

- Management commands: update_translation_projects, updatedb, upgrade, setup


Unmerged Features
^^^^^^^^^^^^^^^^^

These features appeared upstream since we forked, but haven't been
incorporated.

- Extension actions.

- Tags and Goals.

- Local Translation Memory.

- ``assign_permissions`` management command (688b8482)

- Placeables support in the editor (2cb03709 .. 97f92ad3)

- Integration with django-allauth. We use our own auth mechanisms.


Editor Differences
------------------

- Filters allow sorting units according to their last action date.

- TM diffs show what has been removed and what's being added.

- Latest translator comments can be removed/blanked.

- The Wikipedia lookup backend has been removed.


Layout Differences
------------------

- Highly customized layout and look & feel.

- No *Top Contributors* tables.

- User-actionable items are in a navbar drop-down.

- User-friendly public profile editing.


Other Notable Differences
-------------------------

- Different way of handling and caching stats. Different implementation
  for `refresh_stats`.

- Hard dependency differences. Check the *requirements/* directory for
  details.
