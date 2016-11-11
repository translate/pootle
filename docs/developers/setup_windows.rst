.. _setup_windows:

Windows Development Environment Setup
=====================================

.. note:: Ensure that you are executing all of the following steps with
   Administrator privileges!

Install prerequisites
^^^^^^^^^^^^^^^^^^^^^

Download the latest Redis installer from:
    https://github.com/MSOpenTech/redis/releases

During the installation you will be asked to set what port Redis should listen
on; leave it at the default (6379).

Download the latest Nodejs installer from:
    https://nodejs.org/en/

Detailed setup
^^^^^^^^^^^^^^

.. note:: For convenience these instructions consistently specify paths
    ``C:\venv``, ``C:\git\pootle`` and ``C:\temp``, but you can change these to
    suit your environment and needs.

.. note:: Depending on how correctly your environment is set up (depending on
   factors beyond your control such as virus scanners, Windows system health,
   and so on), you may need to use the command ``python -m pip`` for the
   following steps if the basic ``pip`` commands fail. Similarly, any other
   Python command that should 'just work' might need to be invoked with
   ``python -m`` to avoid issues.

For installing the dependencies in an isolated environment, set up a fresh
virtualenv.

.. code-block:: console

    > pip install virtualenv
    > virtualenv C:\venv

Activate the new virtualenv and upgrade pip:

.. code-block:: console

    > C:\venv\Scripts\activate
    (venv)> pip install --upgrade pip setuptools

Clone your fork of the Pootle master using your favourite Windows
implementation of Git so that you have a working copy somewhere accessible on
your computer (e.g. ``C:\git\pootle``).

First, rename ``90-dev-local.conf.sample`` to ``90-dev-local.conf`` (in
``pootle\settings``) to enable a basic configuration suitable for local
hacking.

Then go to the Pootle ``requirements\base.txt`` and comment out the following
packages:

.. code-block:: console

    # lxml
    # python-levenshtein
    # scandir

These three packages are difficult to build on Windows, so we will download
pre-built versions to install manually, saving them into your temporary folder:

- http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml
- http://www.lfd.uci.edu/~gohlke/pythonlibs/#python-levenshtein
- http://www.lfd.uci.edu/~gohlke/pythonlibs/#scandir

Now install them explicitly:

.. code-block:: console

    (venv)> pip install C:\temp\lxml-3.6.4-cp27-cp27m-win32.whl
    (venv)> pip install C:\temp\python_Levenshtein-0.12.0-cp27-none-win32.whl
    (venv)> pip install C:\temp\scandir-1.2-cp27-none-win32.whl

At this point, you may be able to install Pootle and its requirements using the
following command. However, pip installation of requirements may fail with
"directory was not empty" or "file not found" issues, in which case you need to
use the commands in the next note block.

.. code-block:: console

    (venv)> cd C:\git\pootle
    (venv)> pip install -e .[dev]

.. note:: "Directory was not empty" and "file not found" issues come from
   modern versions of Windows' tighter control over permissions for special
   folders. By default, pip stores temporary files in your ``user\AppData``
   folder which may not allow access in all circumstances. By downloading the
   packages to a folder with no special permissions and building and installing
   them from there we can circumvent these problems:
    
    .. code-block:: console
    
        (venv)> pip download -d C:\temp -r requirements\dev.txt -b C:\temp
        (venv)> pip install -r requirements\dev.txt -b C:\temp -t C:\venv\Lib\site-packages\ --no-index --find-links="C:\temp"
        (venv)> cd C:\git\pootle
        (venv)> pip install -e .


Now that all the requirements are lined up, we are ready to initialise Pootle.
You should be able to initialise the Pootle demo database the same way as on a
Linux system.

.. note:: Depending on how successfully your system has engaged the virtual
   environment, you may have to execute ``pootle`` commands with ``python
   manage.py`` from the pootle root folder instead (e.g. ``python manage.py
   migrate`` instead of ``pootle migrate``).

.. code-block:: console

    (venv)> pootle migrate
    (venv)> pootle initdb

Next, you will need to set up the client-side bundles with NPM. It might be
necessary to deactivate the virtual environment or use a separate command
window to perform this step, but it might also 'just work' from within the
venv.

.. code-block:: console

    C:\git\pootle> cd pootle\static\js
    C:\git\pootle\pootle\static\js> npm install

Once NPM install has completed, the actual javascript bundles can be compiled:

.. code-block:: console

    (venv)> cd C:\git\pootle
    (venv)> pootle webpack --dev

The :djadmin:`webpack` command will keep running after it's completed, to
monitor your javascript files for changes so that it can auto-recompile as you
work. You'll need to either exit it with ``Ctrl+C`` once it has settled down,
or else open up a new command prompt and activate your virtual environment
there too.

One last javascript pack needs to be compiled to complete the client-side
preparations:

.. code-block:: console

    (venv)> pootle compilejsi18n

Now create and verify a super-user as normal:

.. code-block:: console

    (venv)> pootle createsuperuser
    [Follow on-screen prompts.]
    (venv)> pootle verify_user [username]

Pootle is now ready to be fired up!

You will need to run one RQWorker and one Pootle server, so you'll need two
command prompt windows (as both will remain active until you disable the
server):

.. code-block:: console

    (venv)> pootle rqworker

.. code-block:: console

    (venv)> pootle runserver

Congratulations, Pootle should now be running comfortably! Happy hacking on
Windows!!
