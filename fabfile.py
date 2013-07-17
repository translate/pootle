#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""Fabric deployment file."""

from os.path import isfile, isdir

from fabric.api import cd, env
from fabric.context_managers import hide, prefix, settings
from fabric.contrib.console import confirm
from fabric.contrib.files import exists, upload_template
from fabric.operations import get, put, require, run, sudo
from fabric.utils import abort


#
# Deployment environments
#


def production(branch=None, repo=None, feature=None):
    """Work on the production environment"""

    try:
        from deploy.production import fabric
    except ImportError:
        abort("Can't load 'production' environment; is PYTHONPATH exported?")

    # Get new settings based on the provided parameters.
    new_settings = _get_new_settings(branch, repo, feature)

    env.update(fabric.get_settings(new_settings))
    env.environment = 'production'


def staging(branch=None, repo=None, feature=None):
    """Work on the staging environment"""

    try:
        from deploy.staging import fabric
    except ImportError:
        abort("Can't load 'staging' environment; is PYTHONPATH exported?")

    # Get new settings based on the provided parameters.
    new_settings = _get_new_settings(branch, repo, feature)

    env.update(fabric.get_settings(new_settings))
    env.environment = 'staging'


def _get_new_settings(branch=None, repo=None, feature=None):
    """Get a new settings dictionary based on the provided parameters."""

    # If no branch is provided then don't return any new settings.
    if branch is None:
        return {}

    # Create new settings based on the provided parameters.
    new_settings = {
        'repo_branch': branch,
    }

    # If a repository is specified.
    if repo is not None:
        new_settings['project_repo'] = repo

    # If the flag for feature-staging server is specified.
    if feature is not None:
        # Replace all occurrences of problematic characters with - character.
        # Basically this is all characters outside alphanumeric characters, dot
        # and hyphen characters.
        import re
        hyphen_branch = re.sub(r'([^A-Za-z0-9.-])', "-", branch)

        new_settings['db_name'] = 'pootle-' + hyphen_branch
        new_settings['project_name'] = 'pootle-' + hyphen_branch
        new_settings['project_url'] = hyphen_branch + '.testing.locamotion.org'

    # Return the new settings.
    return new_settings


#
# Commands
#


def _remove_directories():
    """Removes initial directories"""
    if exists('%(project_path)s' % env):
        sudo('rm -rf %(project_path)s' % env)
    if exists('%(translations_path)s' % env):
        sudo('rm -rf %(translations_path)s' % env)
    if exists('%(repos_path)s' % env):
        sudo('rm -rf %(repos_path)s' % env)


def _init_directories():
    """Creates initial directories"""
    print('\n\nCreating initial directories...')

    _remove_directories()

    sudo('mkdir -p %(project_path)s' % env)
    sudo('mkdir -p %(project_path)s/logs' % env)
    sudo('mkdir -p %(translations_path)s' % env)
    sudo('mkdir -p %(repos_path)s' % env)
    sudo('chmod -R g=u '
         '%(project_path)s %(translations_path)s %(repos_path)s' % env)
    sudo('chown -R %(user)s:%(server_group)s '
         '%(project_path)s %(translations_path)s %(repos_path)s' % env)


def _init_virtualenv():
    """Creates initial virtualenv"""
    print('\n\nCreating virtualenv...')

    run('virtualenv -p %(python)s --no-site-packages %(env_path)s' % env)
    with prefix('source %(env_path)s/bin/activate' % env):
        run('easy_install pip')


def _clone_repo():
    """Clones the Git repository"""
    print('\n\nCloning the repository...')

    run('git clone %(project_repo)s %(project_repo_path)s' % env)


def _update_repo():
    """Updates the Git repository and checks out the specified branch"""
    print('\n\nUpdating repository branch...')

    with cd(env.project_repo_path):
        run('git fetch --all')
        run('git checkout %(repo_branch)s' % env)
        # Reset the branch to be the origin one. This can avoid problems or
        # merge commits when updating a branch that was forced update.
        run('git reset --hard origin/%(repo_branch)s' % env)
    run('chmod -R go=u,go-w %(project_repo_path)s' % env)


def _install_requirements():
    """Installs dependencies defined in the requirements file"""
    print('\n\nInstalling requirements...')

    with prefix('source %(env_path)s/bin/activate' % env):
        run('pip install -r %(project_repo_path)s/requirements/deploy.txt' % env)
    run('chmod -R go=u,go-w %(env_path)s' % env)


def _update_requirements():
    """Updates dependencies defined in the requirements file"""
    print('\n\nUpdating requirements...')

    with prefix('source %(env_path)s/bin/activate' % env):
        run('pip install -U -r %(project_repo_path)s/requirements/deploy.txt' % env)
    run('chmod -R go=u,go-w %(env_path)s' % env)


def bootstrap():
    """Bootstraps a Pootle deployment."""
    require('environment', provided_by=[production, staging])

    if (not exists('%(project_path)s' % env) or
        confirm('\n%(project_path)s already exists. Do you want to continue?'
                % env, default=False)):
            with settings(hide('stdout', 'stderr')):
                _init_directories()
                _init_virtualenv()
                _clone_repo()
                _update_repo()
                _install_requirements()
    else:
        abort('\nAborting.')


def stage_feature():
    """Deploys a Pootle server for testing a feature branch.

    This copies the DB from a previous Pootle deployment.
    """
    require('environment', provided_by=[staging])

    # Run the required commands to deploy a new Pootle instance based on a
    # previous staging one and using the specified branch.
    bootstrap()
    create_db()
    _copy_db()
    update_db()
    deploy_static()
    install_site()
    print('\n\nSuccessfully deployed at:\n\n\thttp://%(project_url)s\n' % env)


def unstage_feature():
    """Remove a Pootle server deployed using the stage_feature command"""
    require('environment', provided_by=[staging])

    # Run the commands for completely removing this Pootle install
    disable_site()
    drop_db()
    _remove_config()
    _remove_directories()
    print('\n\nRemoved Pootle deployment for http://%(project_url)s' % env)


def create_db():
    """Creates a new DB"""
    require('environment', provided_by=[production, staging])

    create_db_cmd = ("CREATE DATABASE `%(db_name)s` "
                     "DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;"
                     % env)
    grant_db_cmd = ("GRANT ALL PRIVILEGES ON `%(db_name)s`.* TO `%(db_user)s`"
                    "@localhost IDENTIFIED BY \"%(db_password)s\"; "
                    "FLUSH PRIVILEGES;"
                    % env)

    print('\n\nCreating DB...')

    with settings(hide('stderr')):
        run(("mysql -u %(db_user)s %(db_password_opt)s -e '" % env) +
            create_db_cmd +
            ("' || { test root = '%(db_user)s' && exit $?; " % env) +
            "echo 'Trying again, with MySQL root DB user'; " +
            ("mysql -u root %(db_root_password_opt)s -e '" % env) +
            create_db_cmd + grant_db_cmd + "';}")


def drop_db():
    """Drops the current DB - losing all data!"""
    require('environment', provided_by=[production, staging])

    print('\n\nDropping DB...')

    if confirm('\nDropping the %s DB loses ALL its data! Are you sure?'
               % (env['db_name']), default=False):
        run("echo 'DROP DATABASE `%s`' | mysql -u %s %s" %
            (env['db_name'], env['db_user'], env['db_password_opt']))
    else:
        abort('\nAborting.')


def setup_db():
    """Runs all the necessary steps to create the DB schema from scratch"""
    require('environment', provided_by=[production, staging])

    syncdb()
    migratedb()
    initdb()


def _copy_db():
    """Copies the data in the source DB into the DB to use for deployment"""
    require('environment', provided_by=[production, staging])

    print('\n\nCloning DB...')

    with settings(hide('stderr'), temp_dump='/tmp/temporary_DB_backup.sql'):
        print('\nDumping DB data...')

        run("mysqldump -u %(db_user)s %(db_password_opt)s %(source_db)s > "
            "%(temp_dump)s"
            " || { test root = '%(db_user)s' && exit $?; "
            "echo 'Trying again, with MySQL root DB user'; "
            "mysqldump -u root %(db_root_password_opt)s %(source_db)s > "
            "%(temp_dump)s;}" % env)

        print('\nLoading data into the DB...')

        run("mysql -u %(db_user)s %(db_password_opt)s %(db_name)s < "
            "%(temp_dump)s"
            " || { test root = '%(db_user)s' && exit $?; "
            "echo 'Trying again, with MySQL root DB user'; "
            "mysql -u root %(db_root_password_opt)s %(db_name)s < "
            "%(temp_dump)s;}" % env)

        run('rm -f %(temp_dump)s' % env)


def syncdb():
    """Runs `syncdb` to create the DB schema"""
    require('environment', provided_by=[production, staging])

    print('\n\nRunning `syncdb` command...')

    with settings(hide('stdout', 'stderr')):
        with cd('%(project_repo_path)s' % env):
            with prefix('source %(env_path)s/bin/activate' % env):
                run('python manage.py syncdb --noinput')


def initdb():
    """Runs `initdb` to initialize the DB"""
    require('environment', provided_by=[production, staging])

    print('\n\nRunning `initdb` command...')

    with settings(hide('stdout', 'stderr')):
        with cd('%(project_repo_path)s' % env):
            with prefix('source %(env_path)s/bin/activate' % env):
                run('python manage.py initdb')


def migratedb():
    """Runs `migrate` to bring the DB up to date with the latest schema"""
    require('environment', provided_by=[production, staging])

    print('\n\nRunning `migrate` command...')

    with settings(hide('stdout', 'stderr')):
        with cd('%(project_repo_path)s' % env):
            with prefix('source %(env_path)s/bin/activate' % env):
                run('python manage.py migrate --noinput')


def update_db():
    """Runs all the necessary (and probably some unnecessary) steps to
    update DB to the latest schema version
    """
    require('environment', provided_by=[production, staging])

    _updatedb()
    syncdb()
    _migrate_fake()
    migratedb()


def _updatedb():
    """Updates database schemas up to Pootle version 2.5"""
    require('environment', provided_by=[production, staging])

    print('\n\nRunning `updatedb` command...')

    with settings(hide('stdout', 'stderr')):
        with cd('%(project_repo_path)s' % env):
            with prefix('source %(env_path)s/bin/activate' % env):
                run('python manage.py updatedb')


def _migrate_fake():
    """Runs `migrate --fake` to convert the DB to migrations"""
    require('environment', provided_by=[production, staging])

    print('\n\nRunning `migrate --fake` command...')

    with settings(hide('stdout', 'stderr')):
        with cd('%(project_repo_path)s' % env):
            with prefix('source %(env_path)s/bin/activate' % env):
                # Don't fake (back to) initial migration if already converted
                run(r"if ! python manage.py migrate --list | grep '(\*) 0001';"
                    "then python manage.py migrate --all --fake 0001; fi")


def upgrade():
    """Runs `upgrade` to upgrade the DB for new Pootle/Translate Toolkit"""
    require('environment', provided_by=[production, staging])

    print('\n\nRunning `upgrade` command...')

    with settings(hide('stdout', 'stderr')):
        with cd('%(project_repo_path)s' % env):
            with prefix('source %(env_path)s/bin/activate' % env):
                run('python manage.py upgrade')


def load_db(dumpfile=None):
    """Loads data from a SQL script to Pootle DB"""
    require('environment', provided_by=[production, staging])

    print('\n\nLoading data into the DB...')

    if dumpfile is not None:
        if isfile(dumpfile):
            remote_filename = '%(project_path)s/DB_backup_to_load.sql' % env

            if (not exists(remote_filename) or
                confirm('\n%s already exists. Do you want to overwrite it?'
                        % remote_filename, default=False)):

                with settings(hide('stderr')):
                    put(dumpfile, remote_filename)
                    run('mysql -u %s %s %s < %s' %
                        (env['db_user'], env['db_password_opt'],
                         env['db_name'], remote_filename))
                    run('rm %s' % (remote_filename))
            else:
                abort('\nAborting.')
        else:
            abort('\nERROR: The file "%s" does not exist. Aborting.' % dumpfile)
    else:
        abort('\nERROR: A (local) dumpfile must be provided. Aborting.')


def dump_db(dumpfile="pootle_DB_backup.sql"):
    """Dumps the DB as a SQL script and downloads it"""
    require('environment', provided_by=[production, staging])

    print('\n\nDumping DB...')

    if isdir(dumpfile):
        abort("dumpfile '%s' is a directory! Aborting." % dumpfile)

    elif (not isfile(dumpfile) or
          confirm('\n%s already exists locally. Do you want to overwrite it?'
                  % dumpfile, default=False)):

        remote_filename = '%s/%s' % (env['project_path'], dumpfile)

        if (not exists(remote_filename) or
            confirm('\n%s already exists. Do you want to overwrite it?'
                    % remote_filename, default=False)):

            with settings(hide('stderr')):
                run('mysqldump -u %s %s %s > %s' %
                    (env['db_user'], env['db_password_opt'],
                     env['db_name'], remote_filename))
                get(remote_filename, '.')
                run('rm %s' % (remote_filename))
        else:
            abort('\nAborting.')
    else:
        abort('\nAborting.')


def update_code():
    """Updates the source code and its requirements"""
    require('environment', provided_by=[production, staging])

    with settings(hide('stdout', 'stderr')):
        _update_repo()
        _update_requirements()


def deploy_static():
    """Runs `collectstatic` to collect all the static files"""
    require('environment', provided_by=[production, staging])

    print('\n\nCollecting static files and building assets...')

    with settings(hide('stdout', 'stderr')):
        with cd('%(project_repo_path)s' % env):
            with prefix('source %(env_path)s/bin/activate' % env):
                run('mkdir -p pootle/assets')
                run('python manage.py collectstatic --noinput --clear')
                run('python manage.py assets build')
    run('chmod -R go=u,go-w %(project_repo_path)s' % env)


def deploy():
    """Updates the code and installs the production site"""
    require('environment', provided_by=[production, staging])

    with settings(hide('stdout', 'stderr')):
        update_code()
        deploy_static()
        install_site()


def install_site():
    """Configures the server and enables the site"""
    require('environment', provided_by=[production, staging])

    with settings(hide('stdout', 'stderr')):
        update_config()
        enable_site()


def update_config():
    """Updates server configuration files"""
    require('environment', provided_by=[production, staging])

    print('\n\nUpdating server configuration...')

    with settings(hide('stdout', 'stderr')):

        # Configure VirtualHost
        upload_template('deploy/%(environment)s/virtualhost.conf' % env,
                        env.vhost_file, context=env, use_sudo=True)

        # Configure WSGI application
        upload_template('deploy/pootle.wsgi',
                        env.wsgi_file, context=env)

        # Configure and install settings
        upload_template('deploy/%(environment)s/settings.conf' % env,
                        '%(project_settings_path)s/90-%(environment)s-local.conf'
                        % env, context=env)


def _remove_config():
    """Removes server configuration files"""
    print('\n\nRemoving server configuration...')

    sudo('rm -rf %(vhost_file)s' % env)
    run('rm -rf %(wsgi_file)s' % env)
    run('rm -rf %(project_settings_path)s/90-%(environment)s-local.conf' % env)


def enable_site():
    """Enables the site"""
    require('environment', provided_by=[production, staging])

    with settings(hide('stdout', 'stderr')):
        _switch_site(True)


def disable_site():
    """Disables the site"""
    require('environment', provided_by=[production, staging])

    with settings(hide('stdout', 'stderr')):
        _switch_site(False)


def _switch_site(enable):
    """Switches site's status to enabled or disabled"""

    action = "Enabling" if enable else "Disabling"
    print('\n\n%s site...' % action)

    env.apache_command = 'a2ensite' if enable else 'a2dissite'
    sudo('%(apache_command)s %(project_name)s' % env)
    sudo('service apache2 reload')


def touch():
    """Reloads daemon processes by touching the WSGI file"""
    require('environment', provided_by=[production, staging])

    print('\n\nRunning `touch`...')

    with settings(hide('stdout', 'stderr')):
        run('touch %(wsgi_file)s' % env)


def compile_translations():
    """Compiles PO translations"""
    require('environment', provided_by=[production, staging])

    print('\n\nCompiling translations...')

    with settings(hide('stdout', 'stderr')):
        with cd(env.project_repo_path):
            with prefix('source %(env_path)s/bin/activate' % env):
                run('python setup.py build_mo')

def mysql_conf():
    """Sets up .my.cnf file for passwordless MySQL operation"""
    require('environment', provided_by=[production, staging])

    print('\n\nSetting up MySQL password configuration...')

    conf_filename = '~/.my.cnf'

    if (not exists(conf_filename) or
        confirm('\n%s already exists. Do you want to overwrite it?'
                % conf_filename, default=False)):

        with settings(hide('stdout', 'stderr')):
            upload_template('deploy/my.cnf', conf_filename, context=env)
            run('chmod 600 %s' % conf_filename)

    else:
        abort('\nAborting.')
