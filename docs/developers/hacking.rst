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
  <https://github.com/translate/pootle/pulls>`_ so that it doesn't interfere in
  current development plans. Also note that adding new features is relatively
  easy, but keeping them updated is harder.


.. _hacking#setup:

Setting up the development environment
--------------------------------------

The minimum software packages you need for setting up a development environment
include `git <http://git-scm.org>`_ and a `Python interpreter
<http://www.python.org>`_ along with the `pip installer
<http://www.pip-installer.org/>`_. Consult the specifics for your operating
system in order to get each package installed successfully.

Once you have the minimums in place, you will need to install Pootle's
dependencies, which come in shape of Python packages. Instead of installing
them system-wide, we recommend using `virtualenv <http://www.virtualenv.org>`_
(and `virtualenvwrapper
<http://www.doughellmann.com/projects/virtualenvwrapper/>`_ for easing the
management of multiple virtualenvs). This way you can install all the
dependencies at specific versions without interfering with system-wide
packages. You can test on different Python/Django versions in parallel as well.

For the impatients:

.. code-block:: bash

    $ sudo pip install virtualenvwrapper
    $ mkvirtualenv <env-name>
    (env-name) $ git clone https://github.com/translate/pootle.git
    (env-name) $ cd pootle
    (env-name) $ pip install -r requirements/dev.txt
    (env-name) $ cd pootle
    (env-name) $ python manage.py runserver

That will leave you with a Pootle development server up and running ready to
start hacking!

.. note::

   If you have a GitHub account, fork the main translate/pootle repository
   and replace the repository URL by your own fork.


Detailed setup
^^^^^^^^^^^^^^

These are essentially the same steps as above but with further details an
explanations.

For installing the dependencies in an isolated environment, we will use
virtualenv — more specifically virtualenvwrapper, which eases the process of
managing and switching between multiple virtual environments. Installing
virtualenwrapper will pull in virtualenv as a dependency.

.. code-block:: bash

    $ sudo pip install virtualenvwrapper

virtualenvwrapper will need to be configured in order to specify where to store
the created environments.

.. code-block:: bash

   $ export WORKON_HOME=~/envs
   $ mkdir -p $WORKON_HOME
   $ source /usr/local/bin/virtualenvwrapper.sh

.. note::

   You may want to add the above-mentioned commands in your ``.bashrc`` file
   (or whatever file your shell uses for initializing user customizations).

Now the commands provided virtualenv and virtualenvwrapper are available, so we
can start creating our virtual environment.

.. code-block:: bash

    $ mkvirtualenv <env-name>

Replace ``<env-name>`` with a meaningful name that describes the environment
you are creating. ``mkvirtualenv`` accepts any options ``virtualenv`` accepts.
We could for example specify to use the Python 2.6 interpreter by passing the
``-p python2.6`` option.

After running ``mkvirtualenv``, the newly created environment is activated. To
activate and deactivate virtual environments simply run ``workon <env-name>``
and ``deactive`` (this needs to be run in an active environment).

Time to clone Pootle's source code repository. The main repository lives under
`translate/pootle in GitHub <https://github.com/translate/pootle/>`_. If you
have a GitHub account, the best idea is to fork the main repository and to
clone your own fork for hacking. Once you know which way you want to continue
forward, just move to a directory where you want to keep the development files
and run ``git clone`` by passing the repository's URL.

.. code-block:: bash

    (env-name) $ git clone https://github.com/translate/pootle.git

This will create a directory named *pootle* where you will find all the files
that constitute Pootle's source code.

Before running the development server, it's necessary to install the software
dependencies/requirements by using pip. For this matter there are some `pip
requirements files <http://www.pip-installer.org/en/latest/requirements.html>`_
within the *requirements* directory. We will install the requirements defined
in *requirements/dev.txt*, which apart from the minimum will pull in some
extras that will ease the development process.

.. code-block:: bash

    (env-name) $ pip install -r requirements/dev.txt

.. note::

   Some dependencies might need to build or compile source code in languages
   other than Python. You may need to install extra packages on your system in
   order to complete the build process and the installation of the required
   packages.


With all the dependencies installed within the virtual environment, Pootle is
almost ready to run. In development environments you probably want to use
settings that vastly differ from those used in production servers.

Head over the :ref:`settings` section in the documentation to learn more about
how settings work in Pootle. Our recommendation is to create a file named
*90-dev-local.conf* in the *settings* directory and keeping there the
customizations made for development-purposes.

Finally, just move to the directory where the ``manage.py`` script resides and
run the development server.

.. code-block:: bash

    (env-name) $ cd pootle
    (env-name) $ python manage.py runserver

Now you can reach the development server in your browser. On your first visit,
Pootle will create the database schema and will calculate stats, which might
take a while on the first time. Once that is done, you can start the
development server anytime by enabling the virtual environment and running the
``manage.py runserver`` command.

Happy hacking!!


.. _hacking#workflow:

Workflow
--------

Any time you want to fix a bug or work on a new feature, create a new local branch::

  $ git checkout -b <my_new_branch>

Then safely work there, create the needed commits and once the work is ready
for being incorporated upstream, either:

- Push the changes to your own GitHub fork and send us a pull request, or

- Create a patch against the ``HEAD`` of the ``master`` branch using ``git
  diff`` or ``git format-patch`` and attach it to the affecting bug.


.. _hacking#committing:

Commits
-------

When creating commits take into account the following:

What to commit
  As far as possible, try to commit individual changes in individual commits.
  Where different changes depend on each other, but are related to different
  parts of a problem / solution, try to commit then in quick succession.

Commit messages
  Begin the commit message with a single short (less than 50 character) line
  summarizing the change, followed by a blank line and then a more thorough
  description.

  If your change fixes a bug in Bugzilla, mention the bug number, and mention
  the commit sha1 in the bug. If you are reverting a previous commit, mention
  the sha1 revision that is being reverted.
