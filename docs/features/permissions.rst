.. _permissions:

User permissions
================

There are several rights which can be assigned to users or to a group of users,
such as to all logged in users. The default site-wide permissions are
configured by the server administrator. These are the permissions that will be
used in each project unless other permissions are configured.


.. _permissions#permissions_precedence:

Permissions precedence
----------------------

Permissions can be customized server-wide, per-language, per-project or
language/project combination (translation project).

Permissions apply recursively, so server-wide permissions will apply to all
languages and projects unless there is a more specific permission. Language
permission applies to all translation projects under that language, etc.


.. _permissions#special_users:

Special users
-------------

Pootle has two special users, *nobody* and *default*, which are used to assign
permissions to more than one user at once. The user *nobody* represents any
non-logged in user, and *default* represents any logged in user.

If a user has permissions assigned to her user account they override any
default permissions even those applied to more specific objects (i.e. a user
who has specific rights on a language will override default rights on
translation projects).

Server administrators can be specified in the users page of the admin section.
Server administrators have full rights on all languages and projects and
override all permissions.


.. _permissions#available_permissions:

Available permissions
---------------------

The following permissions may be set for the server or per language, or
language-project combination:

view
  Limits access to project of language but does not limit it's visibility.

suggest
  The right to :doc:`suggest <suggestions>` a translation for a specific
  string, also implies the right to upload file using suggest only method.

review
  The right to review the suggested translations and accept or reject them, as
  well as the right to reject false positive quality checks

translate
  The right to supply a translation for a specific string or to replace the
  existing one. This implies the right to upload files using the merge method.

archive
  The right to download archives (ZIP files) of a project or directory.

overwrite
  The right to entirely overwrite a file at the time of upload (instead of the
  default behaviour of merging translations)

administrate
  The right to administrate the project or language including administer
  permissions and delegating rights to users (this is not the same as the site
  administrator)

commit
  The right to update or commit a file to the version control system (if the
  files are configured for :doc:`version_control` integration)


.. _permissions#permissions_interface:

Permissions interface
---------------------

Users with administrative rights for languages or translation projects can
access the permissions interface by clicking on the *Permissions* tab on the
language or translation project index pages.

Pootle administrators will find the default permissions interface on the
administration page, at the "Permissions" tab.

The current rights are listed as they are assigned. The user "nobody" refers to
any user that is not logged in (an anonymous, unidentified user). The user
"default" refers to the rights that all logged in users will have by default,
unless other specific rights were assigned to them. The rest of the users are
users of the Pootle server for which non-default rights were assigned.


.. _permissions#changing_permissions:

Changing permissions
^^^^^^^^^^^^^^^^^^^^

In the list of permissions, you can simply select which rights must be assigned
to that user or class of users. You might need to hold down the ``Ctrl`` key of
you keyboard to select multiple rights. Changes will be updated when you submit
the form.


.. _permissions#adding_a_user:

Adding a user
^^^^^^^^^^^^^

To set permissions for a specific user, select the user in the dropdown list
and set the specific rights for that user. This is only necessary if the user
does not yet have their own set of rights defined.

Users who selected the language or project in their profile settings will be
listed as the project or language team. After that follows a list of all
registered users.


.. _permissions#removing_a_user:

Removing a user
^^^^^^^^^^^^^^^

To reset a user's rights to the default rights, select the tick box next to
their name and permissions list. When you submit, their rights will be reset to
the default rights.

.. warning::

    A user with administrative rights can remove his own administrative rights.


.. _permissions#manage-permissions-with-management-commands:

Manage permissions with management commands
-------------------------------------------

.. versionadded:: 2.5.2

The assignment of Pootle permissions can also be handled using management
commands.


.. _permissions#assign-permissions-with-management-command:

Assign permissions with management command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 2.5.2

It is also possible to assign permissions to a given user in a project,
language or translation project using the :ref:`assign_permissions
<commands#assign-permissions>` management command.
