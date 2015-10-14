=====================================
Welcome to the new Pootle 2.7.3 final
=====================================

*Not yet released*

Bugfix release for 2.7.2.


Changes in Requirements
=======================
- Django >= 1.7.10, < 1.8
- Translate Toolkit >= 1.13.0
- Python >= 2.7, < 3.0
- Redis >= 2.8.4
- Django transaction hooks
- Unix-based operating system.


Major Changes
=============

- Pulled latest translations.


Below we provide much more detail. These are by no means exhaustive, view the
`git log <https://github.com/translate/pootle/compare/2.7.2...2.7.3>`_ for
complete information.


Details of changes
==================

- The editor for static pages now highlights the content's markup
  (:issue:`3346`).
- Pulled latest translations.
- :djadmin:`update_tmserver`: renamed :option:`--overwrite` to
  :option:`--refresh`.
- The Apertium MT backend has been dropped.


...and lots of refactoring, new tests, cleanups, improved documentation and of
course, loads of bugs were fixed.


Credits
=======

This release was made possible by the following people:

%CONTRIBUTORS%

And to all our bug finders, testers and translators, a Very BIG Thank You.
