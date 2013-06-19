
Fabric deployment files
=======================

This directory contains sample files that can be used for deploying Pootle
servers in combination with the *fabfile* (``fabfile.py``) present at the
top-level directory of the Pootle repository

The *fabfile* will setup a Pootle server using a Python virtualenv,
running in an Apache server with *mod_wsgi*.

Please read the following for more information:
http://docs.translatehouse.org/projects/pootle/en/latest/server/fabric_deployment.html

The deployment is separated in two different environments:

- Staging environment (*/deploy/staging/* directory)
- Production environment (*/deploy/production/* directory)

This way server administrators can separate their testing and real-world
Pootle servers.


Configuration
-------------

For deploying a Pootle server in any of the desired environments, it is
necessary to put some configuration files in place.

*/deploy/environment/fabric.py*
  Module with settings that will be used in Fabric.

*/deploy/environment/settings.conf*
  Pootle-specific settings for the server (it will override the defaults).

*/deploy/environment/virtualhost.conf*
  Apache VirtualHost configuration file.

All the settings defined in the ``fabric.py`` module will populate the Fabric
``env`` dictionary, making the configuration keys available in the
*settings.conf* and *virtualhost.conf* files. You can use basic Python string
formatting to access the configuration values.

Sample configuration files are provided for reference in this *deploy*
directory. Adapt them to your needs and put them in the right location
(*production* and *staging* subdirectories) before running any Fabric commands.


Other scripts
-------------

Once you have your Fabric configuration set up and have created production and
staging servers, you may be interested in automatically copying data from
production to staging, for testing with live data.  The *update_staging* shell
script is an example of how you can do this (you will probably want to comment
out or delete many parts of the script that aren't relevant to your
deployment).
