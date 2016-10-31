.. _setup_linux:

Linux Development Environment Setup
===================================

The minimum software packages you need for setting up a development environment
include `git <https://git-scm.com/>`_ and a `Python interpreter
<https://www.python.org>`_ along with the `pip installer
<https://pip.pypa.io/en/stable/>`_. Consult the specifics for your operating
system in order to get each package installed successfully.

Once you have the basic requirements in place, you will need to install
Pootle's dependencies, which come in shape of Python packages. Instead of
installing them system-wide, we recommend using `virtualenv
<https://virtualenv.pypa.io/en/latest/>`_ (and `virtualenvwrapper
<https://virtualenvwrapper.readthedocs.io/en/latest/>`_ for easing the
management of multiple virtualenvs). This way you can install all the
dependencies at specific versions without interfering with system-wide
packages. You can test on different Python/Django versions in parallel as well.

Detailed setup
^^^^^^^^^^^^^^

For installing the dependencies in an isolated environment, we will use
virtualenv -- more specifically virtualenvwrapper, which eases the process of
managing and switching between multiple virtual environments. Install
virtualenwrapper as follows for bash (examine `platform specific installation
instructions
<https://virtualenvwrapper.readthedocs.io/en/latest/install.html>`_ for other
environments):

.. code-block:: console

    $ sudo pip install virtualenvwrapper


virtualenvwrapper will need to be configured in order to specify where to store
the created environments:

.. code-block:: console

   $ export WORKON_HOME=~/envs
   $ mkdir -p $WORKON_HOME
   $ source /usr/local/bin/virtualenvwrapper.sh  # Or /usr/bin/virtualenvwrapper.sh


.. note:: You may want to add the above-mentioned commands and environment
   variables to your :file:`.bashrc` file (or whatever file your shell uses for
   initializing user customizations).


Now that the commands provided by virtualenv and virtualenvwrapper are
available, we can create our virtual environment.

.. code-block:: console

    $ mkvirtualenv <env-name>


Replace ``<env-name>`` with a meaningful name that describes the environment
you are creating. :ref:`mkvirtualenv <virtualenvwrapper:command-mkvirtualenv>`
accepts any options that :command:`virtualenv` accepts. We could for example
specify to use the Python 3.3 interpreter by passing the `-p python3.3
<https://virtualenv.pypa.io/en/latest/reference/#cmdoption--python>`_ option.

.. note:: After running :ref:`mkvirtualenv
   <virtualenvwrapper:command-mkvirtualenv>`, the newly created environment is
   activated. To deactivate it just run:

   .. code-block:: console

      (env-name) $ deactivate


   To activate a virtual environment again use :ref:`workon
   <virtualenvwrapper:command-workon>` as follows:

   .. code-block:: console

      $ workon <env-name>


First, upgrade the version of :command:`pip` and :command:`setuptools` as
follows:

.. code-block:: console

   (env-name) $ pip install --upgrade pip setuptools


Time to clone Pootle's source code repository. The main repository lives under
`translate/pootle in GitHub <https://github.com/translate/pootle/>`_.

.. note:: If you have a GitHub account, fork the main ``translate/pootle``
   repository and replace the repository URL with your own fork.

.. code-block:: console

    (env-name) $ git clone https://github.com/translate/pootle.git


Install Pootle and its development dependencies into your virtualenv.  This
makes it easy to run Pootle locally and is needed for various development
actitivies. The ``[dev]`` target will install some extra packages to aid
development (you can examine these in :file:`requirements/dev.txt`).


.. code-block:: console

    (env-name) $ pip install -e .[dev]


.. note:: Some requirements may depend on external packages.  For these you may
   need to install extra packages on your system in order to complete their
   installation.


With all the dependencies installed within the virtual environment, Pootle is
almost ready to run. In development environments you will want to use settings
that vastly differ from those used in production environments.

For that purpose there is a sample configuration file with settings adapted for
development scenarios, :file:`pootle/settings/90-dev-local.conf.sample`. Copy
this file and rename it by removing the *.sample* extension:

.. code-block:: console

    (env-name) $ cp pootle/settings/90-dev-local.conf.sample ~/.pootle/pootle.conf


.. note:: To learn more about how settings work in Pootle read the
   :doc:`settings </server/settings>` documentation.


Once the configuration is in place, you'll need to setup the database
schema and add initial data.

.. code-block:: console

    (env-name) $ pootle migrate
    (env-name) $ pootle initdb


Now ensure that you have built the assets by following the instructions for
:doc:`frontend development </developers/frontend>`.

Finally, run the development server.

.. code-block:: console

    (env-name) $ pootle runserver


Once all is done, you can start the development server anytime by enabling the
virtual environment (using the :ref:`workon <virtualenvwrapper:command-workon>`
command) and running the :djadmin:`pootle runserver <runserver>` command.


Happy hacking!!