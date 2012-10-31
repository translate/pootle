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

To review the quality checks you need to have translation rights for the
project. To find the results, click on the "Review" tab. Clicking on the name
of a test will step you through the translations that fail the test.

To understand the meaning of each test, Pootle displays the failing tests on
the top-right corner of the translation page with a link to the online
documentation. You can also read the detailed descriptions of the
:ref:`pofilter tests <toolkit:test_description>`.


.. _checks#overriding_quality_checks:

Overriding Quality Checks
-------------------------

.. versionadded:: 2.1

It is possible to override the quality check if the translation is correct.
Reviewers are able to remove the check for a certain string to indicate that
the string is correctly translated. This avoids having to recheck the same
checks multiple times.

If the translation is changed, this information is discarded to ensure that the
new translation is tested again for any possible issues.
