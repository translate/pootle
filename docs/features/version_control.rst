.. _version_control:

Integration with Version Control Systems
========================================

Pootle has the ability to integrate with version control systems (also called
revision control systems). Read more on Wikipedia for a general overview of
what a :wp:`Version Control System <Revision_control>` is.


.. _version_control#supported_systems:

Supported systems
-----------------

========================================  ===========
 System                                    Status
========================================  ===========
 :wp:`CVS <Concurrent_Versions_System>`    Supported
 :wp:`Subversion <Apache_Subversion>`      Supported
 :wp:`Darcs`                               Supported
 :wp:`Git <Git_(software)>`                Supported
 :wp:`Bazaar <Bazaar_(software)>`          Supported
 :wp:`Mercurial`                           Supported
========================================  ===========

It should be possible to add other systems fairly easily. Interested
programmers can look at the `versioncontrol
<https://github.com/translate/translate/tree/master/translate/storage/versioncontrol>`_
module.


.. _version_control#preparation:

Preparation
-----------

.. note::
   .. versionchanged:: 2.5
      :setting:`VCS_DIRECTORY` was introduced for separating version control
      directories.  Previously your :setting:`PODIRECTORY` contained your files
      from version control. Separation allows Pootle to work reliably on
      Distributed Version Control Systems (Git, Mercurial, etc).

.. note:: The setup of version control has to be done outside of the Pootle
   admin interface.

To have any sort of integration with version control from within Pootle, it is
necessary to construct the correct file system structure in the
:setting:`VCS_DIRECTORY` as defined in the settings. Any projects integrating
with a version control system have to follow a layout that corresponds to the
:setting:`PODIRECTORY`. The :setting:`VCS_DIRECTORY` is *pootle/repos* by
default and should contain one directory for each project on the server that is
either a clone/checkout for the corresponding Pootle project, or a symlink (or
a directory with symlinks) to the repo somewhere else on the file system.

The :setting:`PODIRECTORY` therefore contains the translation files used during
normal operation of Pootle, and the :setting:`VCS_DIRECTORY` contains "clean"
versions (with no uncommitted changes) that enables the version control
integration. The meta files for the version control system (*CVS/*, *.svn/*,
*.hg*, *.git*, etc.) therefore should be present in :setting:`VCS_DIRECTORY`
for Pootle to perform the integration.

An example layout::

    .../
    |-- po
    |   `-- project1
    |       |-- de.po
    |       |-- fr.po
    |       `-- pt_BR.po
    `-- repos
        `-- project1
            |-- de.po
            |-- fr.po
            `-- pt_BR.po

Here :setting:`VCS_DIRECTORY` is ``.../repos`` and :setting:`PODIRECTORY` is
``.../po``.  The directory ``.../repos/project1`` contains a clean checkout of
the translations from version control.  This is where Pootle will perform any
version control actions such as updates and commits.

The :setting:`VCS_DIRECTORY` should never contain uncommitted changes. Pootle
will bring in changes from the upstream VCS and rely on it succeeding without
conflicts.



.. _version_control#example:

Example
^^^^^^^

::

    $ cd pootle/repos/
    $ svn co https://translate.svn.sourceforge.net/svnroot/translate/src/trunk/Pootle/po/pootle

Now you have the directory *pootle* containing a translation project. If that
directory is now one of your projects registered on the server, the version
control functions should appear for all users with the necessary privileges.
Look for the functions under the actions on the overview page.

.. note:: The summary of steps to add a new project which will use a VCS are:
   
   #. Create a local copy of the repository in :setting:`VCS_DIRECTORY` (for
      example using ``svn checkout`` in Subversion, or ``git clone`` in Git),
   #. Copy the newly created directory, which holds the translation files for
      the new project, from :setting:`VCS_DIRECTORY` to :setting:`PODIRECTORY`,
   #. Add the project via the administration panel. Remember that the project
      code should match the project directory name both in
      :setting:`VCS_DIRECTORY` and :setting:`PODIRECTORY`.
   
   The project will be automatically imported by Pootle.


.. _version_control#how_to_treat_special_directory_layouts:

How to treat special directory layouts
--------------------------------------

There exists some conventions for directories.

========================  =========================================
 Convention                Directory structure                       
========================  =========================================
 Standard convention       :setting:`PODIRECTORY`/project_name/language_code/files.po
 GNU convention            :setting:`PODIRECTORY`/project_name/language_code.po
========================  =========================================

Is the directory structure for the language files of your project different
from the default structure found in the source project?

If yes, then you might consider using symlinking every single language file to
the expected location. The version control support of Pootle will follow these
links. Thus the meta directories of your version control system (e.g.: *.svn/*
or *CVS/*) do not necessarily have to be below your :setting:`VCS_DIRECTORY`
(see your settings for the value of this setting). In this case, everything
under :setting:`VCS_DIRECTORY` for this project must be outside of the
clone/checkout for the project.

You can use an :ref:`hooks#initialize` hook script to automate the creation of
these symlinks whenever languages are added to your project.

If you use symlinks, ensure that the resulting structure under
:setting:`VCS_DIRECTORY` corresponds to the structure under
:setting:`PODIRECTORY`.


.. _version_control#working:

Working with VCS integrated projects
------------------------------------
Once you have added a project with VCS integration to Pootle, if you have the
necessary privileges, you will be able to perform the different version control
functions from the actions section on the translation project overview page.

.. _version_control#updating:

Updating
^^^^^^^^

If you want to update the Pootle copy of the translations with the version that
is currently in version control, a contributor with the 'update' right can
click on the *Update* link for a file which will then perform the update
process.  The project administrator needs to assign the "update" right.

When updating from version control there is the possibility that a third party
could have changed the file (another translator accessing the version control
directly could have made a change).  Traditionally in version control this
would create a file with conflicts.  Those familiar with version control
conflicts will understand that we can't afford to have that as we won't be able
to resolve them.  Therefore Pootle will be conservative and will consider the
version control system to be the authority and any conflicts in the local file
get be converted to suggestions.  These suggestions then need to be reviewed by
a translator with *review* rights.


.. _version_control#committing:

Committing
^^^^^^^^^^

You can commit translation files from within Pootle.  In the case where
authentication is required to submit the translation to version control
(probably almost all relevant systems), there needs to be a non-blocking
authentication method.  Pootle will not be able to commit if a password is
necessary to complete the action. This unfortunately means that it will
probably not be realistic for Pootle to commit with the project admin's
credentials, as this will require his/her private key(s) to be on the Pootle
server.

This usage scenario is more useful for people hosting their own Pootle server
where they are able to setup one commit account on the version control server,
or perhaps one account for each team.  A typical commit message when committing
from Pootle will look something like this::

    Commit from GNOME Pootle by user Sipho.  80 of 100 messages translated (7
    fuzzy).

So it is still possible to see who submitted what and when, and actually
provides some useful statistics in the commit message.  A user must be assigned
'commit' privileges by the project administrator.  If the user has the correct
privileges, they will see a "submit" link next to each file.


.. _version_control#authentication:

Version Control Authentication
++++++++++++++++++++++++++++++

To access the repository of version controlled files (especially for
submitting), it is necessary to configure a non-interactive authentication.
This enables the Pootle server to connect to the version control server and to
submit changes with the appropriate privileges.

The following examples should help the pootle administrator to configure this
authentication properly.


.. _version_control#subversion:

Subversion (HTTP)
"""""""""""""""""

- Add a new user with appropriate privileges to the subversion server, if
  necessary (e.g. read `subversion authorization
  <http://svnbook.red-bean.com/nightly/en/svn.serverconfig.httpd.html#svn.serverconfig.httpd.authz>`_)

- Make sure, that the *pootle user* has write access for `~/.subversion/` to
  store authentication tokens.  The *pootle user* is whichever user is running
  the Pootle application.  When running behind a webserver this might be the
  webserver user. Thus on some systems using Apache that user is *www-data*.

- Do a real ``svn commit`` with the uid of the *pootle user* in order to:

  - Import (possibly) an SSL certificate

  - Store the username and password in the subversion authentication cache (by
    default, the option ``store-passwords`` is enabled in
    `~/.subversion/config`)

- If you start Pootle from an init script, make sure that all necessary
  environment variables are set. ``$HOME`` will be needed to obtain your cached
  authentication information, for example.


From now on, the *pootle user* should use these stored access credentials when
uploading commits for this repository.


.. _version_control#adding:

Adding
^^^^^^

.. versionadded:: 2.5

When a language is initialized from templates, Pootle will check if it is
inside a version control checkout/clone. If it is, it will add the new files as
initialized from the templates, and commit these initial versions. The same is
done when updating against templates at a later stage -- if this introduced any new
files, these will be added to the configured version control system.

A typical commit message when adding from Pootle will look something like
this::

    New files added from Labs Translation Server based on templates
