.. _roadmap:

Pootle Development Roadmap
==========================

This is the Pootle roadmap for the next few iterations.  Don't look here for
small improvements, we're only tracking larger bits of work.


.. _roadmap#november-2013:

Next release (2.5.1) estimated November 2013
--------------------------------------------

- Translation editor:

  - Get rid of page stepping and use only units.

- Tagging (Mozilla):

  - Allow tagging of translation projects to make it easy to classify and sort
    TPs.

- Goals (Mozilla):

  - Group files in a TP into goals.
  - Set priorities for goals.

- Extension actions (Mozilla):

  - Add custom Python extensions exposed on the project Actions menu.


.. _roadmap#april-2014:

Estimated release April 2014
----------------------------

- Move to Django 1.5/1.6 - remove anything keeping us on Django 1.4.
- Live cross project Translation Memory (LibreOffice).
- Stats speedup - work on Stats speedups (LibreOffice).
- Concordance searching (LibreOffice).
- amaGama - automate updating of resources.
- Translation editor improvements:

  - Highlight - terms, variables and other things in source text and allow them
    to be copied easily using the keyboard.
  - Live Quality Assurance checks - at the moment these happen after the
    translation editor has left the unit, performing them while editing will
    help to reduce errors.

- Developer centric changes:

  - Adding a UI test framework.
  - Automatic tests for most important parts of Pootle to prevent the risk of
    regressions.

- Mozilla specific features:

  - Proper plural forms handling in Pootle for Firefox Desktop.
  - Integration of compare-locale errors to the translator error page.

- Contributions by a translator to a given project and language.


.. _roadmap#october-2014:

Estimated release October 2014
------------------------------

- Substring matching in TM.
- Variable abstraction so that we can leverage translations from other projects
  that might not match because of differences in variables placeable e.g.
  ``%s`` vs ``&brandShortName;``.
- Management statistical reporting - project, language and user statistical
  reporting.
- A dashboard (health report) that allows l10n managers to check on the health
  of a language.
- Social interventions:

  - Social sharing of projects, strings, etc for community building and
    community input.
  - Social/Persona authentication to make it easier for users to login and
    contribute.
  - OpenBadges - implement badges to reward team members contributions.

- Team review of translations.
- Easing team management:

  - Improve our rights display.
  - Request a new language.
  - Request to join a translation team.


.. _roadmap#in-the-future:

Sometime in the future
----------------------

Things we'd love to do sooner but they are hard or need a sponsor.

- Get rid of actions for pushing, merging and retrieving translations. Do these
  actions in the background with no human intervention at all to reduce errors,
  improve scale.
- Manage all setup from version control files.
- Monoligual files - make Pootle work more reliably directly on monolingual
  files.
