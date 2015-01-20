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
