
Fabric deployment files
=======================

This directory contains sample files that can be used in combination with
the *fabfile* available in the repository for deploying Pootle servers.

This *fabfile* will setup a Pootle server within a virtual environment,
running in a Apache server with *mod_wsgi*.

Please read the following docs for more information:
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

Sample configuration files are provided for reference under the */deploy/*
directory. Adapt them to your needs and put them in the right location before
running any Fabric commands.
