.. _checks:

Quality checks
==============

Pootle provides a powerful way of reviewing translations for quality. It
exposes most of the :ref:`pofilter tests <toolkit:pofilter_tests>` that can
test for several issues that can affect the quality of your translations.

If Pootle indicates a possible problem with a translation, it doesn't mean that
the translation is necessarily wrong, just that you might want to review it.
Pootle administrators should indicate the correct project type (GNOME, KDE,
Mozilla, etc.) in the administration pages. This will improve the accuracy of
the quality checks.

Critical checks are prominently displayed through the browsing UI. Any
extra failing checks can be accessed by clicking the ``+`` button located
right below the navigation breadcrumbs. Clicking on the name of a test
will step you through the translations that fail the test.

While in the translation editor, submissions resulting in critical failing
checks will be immediately reported, preventing you from automatically
continuing until the issues have been resolved or disregarded as false
positives.

To understand the meaning of each test, Pootle displays the failing tests
right on top of the submission button, with a link to the online
documentation. You can also read the detailed descriptions of the
:ref:`pofilter tests <toolkit:test_description>`.


.. _checks#overriding_quality_checks:

Overriding Quality Checks
-------------------------

It is possible to override the quality check if the translation is correct.
Reviewers are able to remove the check for a certain string to indicate that
the string is correctly translated. This avoids having to recheck the same
checks multiple times.

If the translation is changed, this information is discarded to ensure that the
new translation is tested again for any possible issues.
