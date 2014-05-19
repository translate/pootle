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

- Commands and store action logging.

- New management commands: ``revision``, ``changed_languages``,
  ``test_checks``, ``refresh_scores``.

- User scores and rating based on submission similarities.

- Whole new set of quality checks (plus the related ``test_checks``
  management command).

- Screenshot prefix URL to allow integrating screenshots for units.

- Projects and Translation Projects can be disabled.

- Evernote-specific apps: reports.

- Landing page for anonymous users.

- Ability to list top scorers over a period of time.


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

- Management commands: updatedb, upgrade, setup

- Page zoom.


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


Other Notable Differences
-------------------------

- Hard dependency differences. Check the *requirements/* directory for
  details.


Features Merged Back to Upstream
--------------------------------

Some of the work done in our fork has been merged back to upstream. Some
of these might contain small differences, mostly because
Pootle-as-a-product has different business needs.

Added Features
^^^^^^^^^^^^^^

- Report target field has been removed. This functionality has been
  integrated into a new contact form.

- Table sorting is remembered across overview pages.

- Captcha implementation details have been refined.

- General *system* user which is the author of the batch actions performed
  via management commands.

- Timeline tracks all changes done to units.

- Project-specific announcements in a sidebar.

- Maintenance mode middleware. It can be enabled in the settings before
  performing any app upgrades.

Removed Features
^^^^^^^^^^^^^^^^

- Removed Live Translation.

- Removed support for autosync.

Editor Differences
^^^^^^^^^^^^^^^^^^

- Non-admin users can't submit units in fuzzy state.

- If the currently-submitted unit has pending checks, the editor won't
  advance to the next unit and it will be updated displaying the
  unresolved checks.

- Quality checks can be individually muted/unmuted.

- The *Submit*/*Suggest* button is not enabled until a change over the
  initial state of the unit is detected.

- When going through all units in the translation editor, users will be
  automatically redirected back to overview.


Layout Differences
^^^^^^^^^^^^^^^^^^

- Redesigned navigation scheme, including fast, easy and practical
  navigation via breadcrumb drop-downs.

- Tabs have been replaced in favor of drop-down menus.

- Critical errors are prominently displayed.

- No home page. Users are redirected to their preferred language pages
  instead, falling back to the project listings page.

- Single-column and wide browsing table.

- All templates are gathered in a single location (*pootle/templates*),
  and have been reorganized and sorted.

- `Modern browser support <browsers>`_. This includes latest stable
  versions of major browsers, and therefore some JavaScript libraries
  that don't rely on old browsers can be used (namely jQuery 2.x). Some
  CSS prefixes have been removed too.

Other Notable Differences
^^^^^^^^^^^^^^^^^^^^^^^^^

- URLs have been unified and all follow the same scheme. URLs ending in
  *.html* have been removed altogether. ``reverse()`` and ``{% url %}``
  are used almost everywhere.
