.. _hacking:

Hacking
=======

Want to fix a bug in Pootle? Want to change the behaviour of an existing
feature or add new ones? This section is all about hacking on Pootle, so if you
are interested on the topic, keep reading.


.. _hacking#before:

Before doing anything
---------------------

Before starting any actual work on the source code, make sure that:

- There is nobody working on the bug you are trying to fix. See the `existing
  bug reports <https://github.com/translate/pootle/issues>`_ and the `existing
  pull requests <https://github.com/translate/pootle/pulls>`_. In the situation
  where somebody else is working on a fix, you can always offer your help.

- If you plan to develop a new feature and want to include it upstream, please
  first discuss it with the developers on the `Pootle development channel
  <https://gitter.im/translate/dev>`_ or in the `translate-pootle mailing list
  <https://lists.sourceforge.net/lists/listinfo/translate-pootle>`_ so that it
  doesn't interfere in current development plans. Also note that adding new
  features is relatively easy, but keeping them updated is harder.


.. _hacking#setup:

Environment setup
-----------------

Although Pootle should only be deployed to production on a Linux server, it is possible to get a viable 
development environment up and running on Windows with some slightly different steps.

- :ref:`Environment setup on Linux <setup_linux>`
- :ref:`Environment setup on Windows <setup_windows>`


.. _hacking#workflow:

Workflow
--------

Any time you want to fix a bug or work on a new feature, create a new local
branch:

.. code-block:: console

  $ git checkout -b <my_new_branch>


Then safely work there, create the needed commits and once the work is ready
for being incorporated upstream, either:

- Push the changes to your own GitHub fork and send us a pull request, or

- Create a patch against the ``HEAD`` of the ``master`` branch using
  :command:`git diff` or :command:`git format-patch` and attach it to the
  affected issue.


.. _hacking#committing:

Commits
-------

When creating commits take into account the following:

What to commit
  As far as possible, try to commit individual changes in individual commits.
  Where different changes depend on each other, but are related to different
  parts of a problem / solution, try to commit them in quick succession.

  If a change in the code requires some change in the documentation then all
  those changes must be in the same commit.

  If code and documentation changes are unrelated then it is recommended to put
  them in separate commits, despite that sometimes it is acceptable to mix
  those changes in the same commit, for example cleanups changes both in code
  and documentation.

Commit messages
  Begin the commit message with a single short (less than 50 character) line
  summarizing the change, followed by a blank line and then a more thorough
  (and sometimes optional) description.

  ::

    Cleanups


  Another example:

  ::

    Factor out common behavior for whatever

    These reduces lines of code to maintain, and eases a lot the maintenance
    work.

    Also was partially reworked to ease extending it in the future.


  If your change fixes a bug in the tracker, mention the bug number. This way the
  bug is automatically closed after merging the commit.

  ::

    Docs: Update code for this thing

    Now the docs are exact and represent the actual behavior introduced in
    commits ef4517ab and abc361fd.

    Fixes #2399

  If you are reverting a previous commit, mention the sha1 revision that is
  being reverted.

  ::

    Revert "Fabric: Cleanup to use the new setup command"

    This reverts commit 5c54bd4.
