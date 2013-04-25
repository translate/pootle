.. _hooks:

Hooks
=====

Pootle supports hooks to customize its behavior at various points in its
interaction with :doc:`Version Control Systems <version_control>`,
translation update and translation initialization.

Hooks are Python scripts and can do things like checking or converting
formats before commit.

.. note:: See `bug 2559 <http://bugs.locamotion.org/show_bug.cgi?id=2559>`_ tracking changes
   needed for hooks to run on Pootle 2.5.


.. _hooks#implementing:

Implementing a hook
-------------------
Hooks are Python scripts stored in the *pootle/scripts* directory and are
named after their project name.  Thus, *hello.py* for a project called
**hello**.

The project hook should implement functions for each needed hooktype.


.. _hooks#hooktypes:

Available hooktypes
-------------------

+-------------------+---------------------------+-----------------------------------------------------------------+
| Hooktype          | Arguments                 | Return                                                          |
+===================+===========================+=================================================================+
| initialize        | projectdir, languagecode  | *unused*                                                        |
+-------------------+---------------------------+-----------------------------------------------------------------+
| precommit         | file, author, message     | array of strings indicating what files to commit                |
+-------------------+---------------------------+-----------------------------------------------------------------+
| postcommit        | file, success             | *unused*                                                        |
+-------------------+---------------------------+-----------------------------------------------------------------+
| preupdate         | file                      | pathname of file to update                                      |
+-------------------+---------------------------+-----------------------------------------------------------------+
| postupdate        | file                      | *unused*                                                        |
+-------------------+---------------------------+-----------------------------------------------------------------+
| pretemplateupdate | file                      | boolean indicating whether file should be updated from template |
+-------------------+---------------------------+-----------------------------------------------------------------+
