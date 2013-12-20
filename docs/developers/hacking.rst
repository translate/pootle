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
  bug reports
  <http://bugs.locamotion.org/buglist.cgi?list_id=983&resolution=---&query_format=advanced&bug_status=UNCONFIRMED&bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&product=Pootle>`_
  and the `existing pull requests
  <https://github.com/translate/pootle/pulls>`_. In the situation where
  somebody else is working on a fix, you can always offer your help.

- If you plan to develop a new feature and want to include it upstream, please
  first discuss it with the developers `on IRC
  <irc://irc.freenode.net/#pootle>`_ or in the `translate-pootle mailing list
  <https://lists.sourceforge.net/lists/listinfo/translate-pootle>`_ so that it
  doesn't interfere in current development plans. Also note that adding new
  features is relatively easy, but keeping them updated is harder.


.. _hacking#setup:

Setting up the development environment
--------------------------------------

The minimum software packages you need for setting up a development environment
include `git <http://git-scm.org>`_ and a `Python interpreter
<http://www.python.org>`_ along with the `pip installer
<http://www.pip-installer.org/>`_. Consult the specifics for your operating
system in order to get each package installed successfully.

Once you have the basic requirements in place, you will need to install
Pootle's dependencies, which come in shape of Python packages. Instead of
installing them system-wide, we recommend using `virtualenv
<http://www.virtualenv.org>`_ (and `virtualenvwrapper
<http://www.doughellmann.com/projects/virtualenvwrapper/>`_ for easing the
management of multiple virtualenvs). This way you can install all the
dependencies at specific versions without interfering with system-wide
packages. You can test on different Python/Django versions in parallel as well.


.. _hacking#detailed-setup:

Detailed setup
^^^^^^^^^^^^^^

For installing the dependencies in an isolated environment, we will use
virtualenv -- more specifically virtualenvwrapper, which eases the process of
managing and switching between multiple virtual environments. Installing
virtualenwrapper will pull in virtualenv as a dependency.

.. code-block:: bash

    $ sudo pip install virtualenvwrapper


virtualenvwrapper will need to be configured in order to specify where to store
the created environments.

.. code-block:: bash

   $ export WORKON_HOME=~/envs
   $ mkdir -p $WORKON_HOME
   $ source /usr/local/bin/virtualenvwrapper.sh  # Or /usr/bin/virtualenvwrapper.sh


.. note:: You may want to add the above-mentioned commands in your
   :file:`.bashrc` file (or whatever file your shell uses for initializing user
   customizations).


Now the commands provided virtualenv and virtualenvwrapper are available, so we
can start creating our virtual environment.

.. code-block:: bash

    $ mkvirtualenv <env-name>


Replace ``<env-name>`` with a meaningful name that describes the environment
you are creating. :command:`mkvirtualenv` accepts any options that
:command:`virtualenv` accepts. We could for example specify to use the Python
2.6 interpreter by passing the :option:`-p python2.6` option.

.. note:: After running :command:`mkvirtualenv`, the newly created environment
    is activated. To deactivate it just run:

    .. code-block:: bash

      (env-name) $ deactivate


    To activate a virtual environment again simply run:

    .. code-block:: bash

      $ workon <env-name>


Time to clone Pootle's source code repository. The main repository lives under
`translate/pootle in GitHub <https://github.com/translate/pootle/>`_. If you
have a GitHub account, the best idea is to fork the main repository and to
clone your own fork for hacking. Once you know which way you want to continue
forward, just move to a directory where you want to keep the development files
and run :command:`git clone` by passing the repository's URL.

.. code-block:: bash

    (env-name) $ git clone https://github.com/translate/pootle.git


This will create a directory named :file:`pootle` where you will find all the
files that constitute Pootle's source code.

.. note:: If you have a GitHub account, fork the main ``translate/pootle``
   repository and replace the repository URL by your own fork.


Before running the development server, it's necessary to install the software
dependencies/requirements by using pip. For this matter there are some `pip
requirements files <http://www.pip-installer.org/en/latest/requirements.html>`_
within the :file:`requirements` directory. We will install the requirements
defined in :file:`requirements/dev.txt`, which apart from the minimum will pull
in some extras that will ease the development process.

.. code-block:: bash

    (env-name) $ cd pootle
    (env-name) $ pip install -r requirements/dev.txt


.. note:: Some dependencies might need to build or compile source code in
   languages other than Python. You may need to install extra packages on your
   system in order to complete the build process and the installation of the
   required packages.


With all the dependencies installed within the virtual environment, Pootle is
almost ready to run. In development environments you will want to use settings
that vastly differ from those used in production environments.

For that purpose there is a sample configuration file with settings adapted for
development scenarios, :file:`pootle/settings/90-dev-local.conf.sample`. Copy
this file and rename it by removing the *.sample* extension:

.. code-block:: bash

    (env-name) $ cp pootle/settings/90-dev-local.conf.sample pootle/settings/90-dev-local.conf


.. note:: To learn more about how settings work in Pootle head over the
  :ref:`settings` section in the documentation.


Once the configuration is in place, you'll need to setup the database
schema and add initial data.

.. code-block:: bash

    (env-name) $ python manage.py syncdb --noinput
    (env-name) $ python manage.py migrate
    (env-name) $ python manage.py initdb


Finally, just run the development server.

.. code-block:: bash

    (env-name) $ python manage.py runserver


Once all is done, you can start the development server anytime by enabling the
virtual environment (using the :command:`workon` command) and running the
:command:`manage.py runserver` command.

Happy hacking!!


.. _hacking#workflow:

Workflow
--------

Any time you want to fix a bug or work on a new feature, create a new local
branch:

.. code-block:: bash

  $ git checkout -b <my_new_branch>


Then safely work there, create the needed commits and once the work is ready
for being incorporated upstream, either:

- Push the changes to your own GitHub fork and send us a pull request, or

- Create a patch against the ``HEAD`` of the ``master`` branch using
  :command:`git diff` or :command:`git format-patch` and attach it to the
  affected bug.


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


  If your change fixes a bug in Bugzilla, mention the bug number. This way the
  bug is automatically closed after merging the commit.

  ::

    Docs: Update code for this thing

    Now the docs are exact and represent the actual behavior introduced in
    commits ef4517ab and abc361fd.

    Fixes bug #2399

  If you are reverting a previous commit, mention the sha1 revision that is
  being reverted.

  ::

    Revert "Fabric: Cleanup to use the new setup command"

    This reverts commit 5c54bd4.
