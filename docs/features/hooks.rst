.. _hooks:

Hooks
=====

Pootle supports hooks to customize its behavior at various points in its
interaction with :doc:`Version Control Systems <version_control>`,
translation update, and translation initialization.

Hooks are Python scripts and can do things like checking or converting
formats before commit.

.. note::
  .. versionchanged:: 2.5

  Because VCS checkouts and commits are performed in a separate
  :setting:`VCS_DIRECTORY`, hooks performing VCS operations themselves may
  need to use functions in ``apps.pootle_misc.versioncontrol`` to copy files
  between that directory and the :setting:`PODIRECTORY` containing translation
  files. As part of this change, pathnames passed to hooks are relative to
  :setting:`PODIRECTORY`, not absolute paths.

.. _hooks#implementing:

Implementing a hook
-------------------
Hooks are Python scripts stored in the *pootle/scripts* directory with the
same name as a project.  Thus, ``hello.py`` for a project called
**hello**.

The project hook should implement functions for each needed hooktype.


.. _hooks#hooktypes:

Available hooktypes
-------------------

+-----------------------+---------------------------+-----------------------------------------------------------------+
| Hooktype              | Arguments                 | Return                                                          |
+=======================+===========================+=================================================================+
| ``initialize``        | projectdir, languagecode  | *unused*                                                        |
+-----------------------+---------------------------+-----------------------------------------------------------------+
| ``precommit``         | file, author, message     | array of strings indicating what files to commit                |
+-----------------------+---------------------------+-----------------------------------------------------------------+
| ``postcommit``        | file, success             | *unused*                                                        |
+-----------------------+---------------------------+-----------------------------------------------------------------+
| ``preupdate``         | file                      | pathname of file to update                                      |
+-----------------------+---------------------------+-----------------------------------------------------------------+
| ``postupdate``        | file                      | *unused*                                                        |
+-----------------------+---------------------------+-----------------------------------------------------------------+
| ``pretemplateupdate`` | file                      | boolean indicating whether file should be updated from template |
+-----------------------+---------------------------+-----------------------------------------------------------------+

.. _hooks#initialize:

initialize
----------

This hook is called when a language is added to a project. It can be used to
set up any additional files that may be needed (e.g. alternate formats) or
even handle repositories with special directory layouts, by adding appropriate
symlinks in the :setting:`VCS_DIRECTORY`.

The first parameter is the path to the project directory. It's up to this
script to know any internal structure of the directory (in particular whether
standard, GNU, or a special
:ref:`tree style <version_control#how_to_treat_special_directory_layouts>`
is used).

The second parameter is the code for the language (e.g. ``nl``, ``pt-BR``,
``sr_RS@latin`` etc.) that is being added to the project.

.. _hooks#precommit:

precommit
---------

This hook is called when a translation file for a project is
:ref:`committed <version_control#committing>` to VCS (possibly as a result of
an :ref:`update against templates <templates#updating_against_templates>` that
added a new file, in which case it is called after the ``pretemplateupdate``
hook). It can be used to perform conversion to another format and other
pre-commit checks and fixups.

The first parameter is the path to the file that will be committed. The second
parameter is the author what will be used for the commit, and the third argument
is the commit message.

This hook should return an array (possibly empty) of filenames that should also
be commmitted together with the translation file.

.. _hooks#postcommit:

postcommit
----------

This hook is called under the same circumstances as the ``precommit`` hook,
after the commit operation has been attempted.  It can be used to do logging
or cleanup of resources created by the precommit hook.

The first parameter is the path to the file that will be committed. The second
parameter is a boolean indicating whether the commit was successful.

.. _hooks#preupdate:

preupdate
---------

This hook is called when a translation file for a project is
:ref:`updated <version_control#updating>` from VCS.  It can be used to
set up for conversion from another format in the project source files.

The first (and only) parameter is the path to the translation file that will be
updated.

This hook should return the filename that will be updated. Normally this
should be identical to the filename parameter passed to the hook, but if format
conversion is needed, this can be another (project source) file to be updated
instead, so that the ``postupdate`` hook can use it to generate the Pootle
translation file.

.. _hooks#postupdate:

postupdate
----------

This hook is called under the same circumstances as the ``preupdate`` hook,
after the update has been completed (if the update fails, a VersionControlError
is raised and this hook is not called).  It can be used to do format conversion
to generate Pootle translation files from project source formats as well as
other logging.

The first parameter is the path to the file that was updated.

.. note::

  If a ``preupdate`` hook changes the file to be updated (by returning a string
  other than the filename it is passed) the original filename, not the modified
  one it returns, will be passed to the ``postupdate`` hook, if there is one.

.. _hooks#pretemplateupdate:

pretemplateupdate
-----------------

.. versionadded:: 2.5.1

This hook is called when a translation file for a project is
:ref:`updated against templates <templates#updating_against_templates>` to
get new source strings (and mark removed strings as obsolete). It can be used to
customize the handling of new or obsolete strings or to prevent updating
against templates for any reason.

The first parameter is the path to the template file that will be used to update
the translation file. If the hook returns false, that template file will not be
used to generate updates for translation files
