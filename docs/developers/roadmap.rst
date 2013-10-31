Pootle Development Roadmap
==========================

This is the Pootle roadmap for the next few iterations.  Don't look here for
small improvements, we're only tracking larger bits of work.

Next - 2.5.1 - estimated October 2013
-------------------------------------
- Editor
  - Get rid of page stepping and use only units
- Tagging (Mozilla)
  - Allow tagging of translation projects to make it easy to classify and sort
    TPs 
- Goals (Mozilla)
  - Group files in a TP into goals
  - Set priorities for goals
- Extension actions (Mozilla)
  - add custom Python extensions exposed on the project Actions menu


Next+1 - 2.5.2 - estimated April 2014
-----------------------------------
- Move to Django 1.5 - remove anything keeping us on Django 1.4
- UI testing framework
- Live cross project Translation Memory (LibreOffice)
- Stats speedup - work on Stats speedups (LibreOffice)
- Concordance searching (LibreOffice)
- Amagama - automate updating of resources
- Editor improvements
  - Highlight: terms, variables and other things in source text and allow them
    to be copied easily using the keyboard
  - Live Quality Assurance checks - at the moment these happen after the
    translator has left the unit, performing them while editing will help to
    reduce errors
- Developer centric changes
  - Adding a UI test framework
  - Automatic tests for most important parts of Pootle to prevent the risk of
    regressions.
- Mozilla specific features
  - Proper plural forms handling in Pootle for Firefox Desktop
  - Integration of compare-locale errors to the translator error page
- Contributions by a translator to a given project and language


Next+2 - estimated October 2014
-------------------------------
- Move to Django 1.6
- Substring matching in TM
- Variable abstraction so that we can leverage translations from other projects
  that might not match because of differences in variables placeable e.g. %s vs
  &brandShortName;
- Management statistical reporting - project, language and user statistical
  reporting
- A dashboard (health report) that allows l10n managers to check on the health
  of a language.
- Social interventions
  - Social sharing of projects, strings, etc for community building and community
    input
  - Social/Persona authentication to make it easier for users to login and
    contribute
  - OpenBadges - implement badges to reward team members contributions
- Team review of translations
- Easing team management
  - Improve our rights display
  - Request a new language
  - Request to join a translation team


Sometime in the future
----------------------
Things we'd love to do sooner but they are hard or need a sponsor.

- Get rid of actions for pushing, merging and retrieving translations.  Do
  these actions in the background with no human intervention at all to reduce
  errors, improve scale.
- Manage all setup from version control files.
- Monoligual files - make Pootle work more reliably directly on monolingual files
