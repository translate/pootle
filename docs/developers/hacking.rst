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

Setting up the development environment
--------------------------------------

The minimum software packages you need for setting up a development environment
include `git <http://git-scm.com/>`_ and a `Python interpreter
<https://www.python.org>`_ along with the `pip installer
<https://pip.pypa.io/en/stable/>`_. Consult the specifics for your operating
system in order to get each package installed successfully.

Once you have the basic requirements in place, you will need to install
Pootle's dependencies, which come in shape of Python packages. Instead of
installing them system-wide, we recommend using `virtualenv
<https://virtualenv.pypa.io/en/latest/>`_ (and `virtualenvwrapper
<https://bitbucket.org/dhellmann/virtualenvwrapper>`_ for easing the
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

.. code-block:: console

    $ sudo pip install virtualenvwrapper


virtualenvwrapper will need to be configured in order to specify where to store
the created environments.

.. code-block:: console

   $ export WORKON_HOME=~/envs
   $ mkdir -p $WORKON_HOME
   $ source /usr/local/bin/virtualenvwrapper.sh  # Or /usr/bin/virtualenvwrapper.sh


.. note:: You may want to add the above-mentioned commands and environment
   variables to your :file:`.bashrc` file (or whatever file your shell uses for
   initializing user customizations).


Now that the commands provided by virtualenv and virtualenvwrapper are
available, we can start creating our virtual environment.

.. code-block:: console

    $ mkvirtualenv <env-name>


Replace ``<env-name>`` with a meaningful name that describes the environment
you are creating. :command:`mkvirtualenv` accepts any options that
:command:`virtualenv` accepts. We could for example specify to use the Python
2.6 interpreter by passing the `-p python2.6
<https://virtualenv.pypa.io/en/latest/reference.html#cmdoption--python>`_
option.

.. note:: After running :command:`mkvirtualenv`, the newly created environment
   is activated. To deactivate it just run:

   .. code-block:: console

      (env-name) $ deactivate


   To activate a virtual environment again simply run:

   .. code-block:: console

      $ workon <env-name>


Time to clone Pootle's source code repository. The main repository lives under
`translate/pootle in GitHub <https://github.com/translate/pootle/>`_.

.. note:: If you have a GitHub account, fork the main ``translate/pootle``
   repository and replace the repository URL with your own fork.

.. code-block:: console

    (env-name) $ git clone https://github.com/translate/pootle.git


Next, install Pootle software dependencies using :command:`pip`.  The
requirements are stored in the :file:`requirements` directory. The
:file:`dev.txt` requirements will install some extra packages to aid
development.


.. code-block:: console

    (env-name) $ cd pootle
    (env-name) $ pip install -r requirements/dev.txt


.. note:: Some requirements may depend on external packages.  For these you may
   need to install extra packages on your system in order to complete their
   installation.

Install Pootle into your virtualenv.  This makes it easy to run Pootle locally
and is needed for various development actitivies.

.. code-block:: console

    (env-name) $ pip install -e .


With all the dependencies installed within the virtual environment, Pootle is
almost ready to run. In development environments you will want to use settings
that vastly differ from those used in production environments.

For that purpose there is a sample configuration file with settings adapted for
development scenarios, :file:`pootle/settings/90-dev-local.conf.sample`. Copy
this file and rename it by removing the *.sample* extension:

.. code-block:: console

    (env-name) $ cp pootle/settings/90-dev-local.conf.sample pootle/settings/90-dev-local.conf


.. note:: To learn more about how settings work in Pootle read the
   :doc:`settings </server/settings>` documentation.


Once the configuration is in place, you'll need to setup the database
schema and add initial data.

.. code-block:: console

    (env-name) $ python manage.py migrate
    (env-name) $ python manage.py initdb


Now ensure that you have built the assets by following the instructions for
:doc:`frontend development </developers/frontend>`.

Finally, run the development server.

.. code-block:: console

    (env-name) $ python manage.py runserver


Once all is done, you can start the development server anytime by enabling the
virtual environment (using the :command:`workon` command) and running the
:djadmin:`manage.py runserver <runserver>` command.


Happy hacking!!


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
