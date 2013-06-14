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

from os.path import isfile

from fabric.api import cd, env
from fabric.context_managers import hide, prefix, settings
from fabric.contrib.console import confirm
from fabric.contrib.files import exists, upload_template
from fabric.operations import require, run, sudo, put, get


#
# Deployment environments
#


def production():
    """Work on the production environment"""

    try:
        from deploy.production import fabric
    except ImportError:
        print("Unable to load 'production' environment - is PYTHONPATH set?")
        exit(1)
        
    env.update(fabric.SETTINGS)
    env.environment = 'production'


def staging():
    """Work on the staging environment"""

    try:
        from deploy.staging import fabric
    except ImportError:
        print("Unable to load 'staging' environment - is PYTHONPATH set?")
        exit(1)

    env.update(fabric.SETTINGS)
    env.environment = 'staging'


#
# Commands
#


def _init_directories():
    """Creates initial directories"""
    if exists('%(project_path)s' % env):
        sudo('rm -rf %(project_path)s' % env)
    if exists('%(translations_path)s' % env):
        sudo('rm -rf %(translations_path)s' % env)
    if exists('%(repos_path)s' % env):
        sudo('rm -rf %(repos_path)s' % env)

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
    run('virtualenv -p %(python)s --no-site-packages %(env_path)s' % env)
    with prefix('source %(env_path)s/bin/activate' % env):
        run('easy_install pip')


def _clone_repo():
    """Clones the Git repository"""
    run('git clone %(project_repo)s %(project_repo_path)s' % env)


def _checkout_repo(branch="master"):
    """Updates the Git repository and checks out the specified branch"""
    with cd(env.project_repo_path):
        run('git checkout master')
        run('git pull')
        run('git checkout %s' % branch)
    run('chmod -R go=u,go-w %(project_repo_path)s' % env)


def _install_requirements():
    """Installs dependencies defined in the requirements file"""
    with prefix('source %(env_path)s/bin/activate' % env):
        run('pip install -r %(project_repo_path)s/requirements/deploy.txt' % env)
    run('chmod -R go=u,go-w %(env_path)s' % env)


def _update_requirements():
    """Updates dependencies defined in the requirements file"""
    with prefix('source %(env_path)s/bin/activate' % env):
        run('pip install -U -r %(project_repo_path)s/requirements/deploy.txt' % env)
    run('chmod -R go=u,go-w %(env_path)s' % env)


def bootstrap(branch="master"):
    """Bootstraps a Pootle deployment using the specified branch"""
    require('environment', provided_by=[production, staging])

    if (not exists('%(project_path)s' % env) or
        confirm('\n%(project_path)s already exists. Do you want to continue?'
                % env, default=False)):

            print('Bootstrapping initial directories...')

            with settings(hide('stdout', 'stderr')):
                _init_directories()
                _init_virtualenv()
                _clone_repo()
                _checkout_repo(branch=branch)
                _install_requirements()
    else:
        print('Aborting.')


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

    with settings(hide('stderr')):
        run(("mysql -u %(db_user)s %(db_password_opt)s -e '" % env) +
            create_db_cmd +
            ("' || { test root = '%(db_user)s' && exit $?; " % env) +
            "echo 'Trying again, with MySQL root DB user'; "
            "mysql -u root %(db_root_password_opt)s -e '" +
            create_db_cmd + grant_db_cmd + "';}")


def setup_db():
    """Runs all the necessary steps to create the DB schema from scratch"""
    require('environment', provided_by=[production, staging])

    with settings(hide('stdout', 'stderr')):
        syncdb()
        initdb()
        migratedb()


def syncdb():
    """Runs `syncdb` to create the DB schema"""
    require('environment', provided_by=[production, staging])

    with settings(hide('stdout', 'stderr')):
        with cd('%(project_repo_path)s' % env):
            with prefix('source %(env_path)s/bin/activate' % env):
                run('python manage.py syncdb --noinput')


def initdb():
    """Runs `initdb` to initialize the DB"""
    require('environment', provided_by=[production, staging])

    with settings(hide('stdout', 'stderr')):
        with cd('%(project_repo_path)s' % env):
            with prefix('source %(env_path)s/bin/activate' % env):
                run('python manage.py initdb')


def migratedb():
    """Runs `migrate` to bring the DB schema up to date"""
    require('environment', provided_by=[production, staging])

    with settings(hide('stdout', 'stderr')):
        with cd('%(project_repo_path)s' % env):
            with prefix('source %(env_path)s/bin/activate' % env):
                run('python manage.py migrate')


def update_db():
    """Updates database schemas up to the latest version"""
    require('environment', provided_by=[production, staging])

    with settings(hide('stdout', 'stderr')):
        _updatedb()
        migratedb()


def _updatedb():
    """Updates database schemas up to Pootle version 2.5"""
    require('environment', provided_by=[production, staging])

    with settings(hide('stdout', 'stderr')):
        with cd('%(project_repo_path)s' % env):
            with prefix('source %(env_path)s/bin/activate' % env):
                run('python manage.py updatedb')


def load_db(dumpfile=None):
    """Loads data from a SQL script to Pootle DB"""
    require('environment', provided_by=[production, staging])

    if dumpfile is not None:
        if isfile(dumpfile):
            remote_filename = '%(project_path)s/DB_backup_to_load.sql' % env

            if (not exists(remote_filename) or
                confirm('\n%s already exists. Do you want to overwrite it?'
                        % remote_filename, default=False)):

                print('\nLoading data into the DB...')

                with settings(hide('stderr')):
                    put(dumpfile, remote_filename)
                    run('mysql -u %s %s %s < %s' %
                        (env['db_user'], env['db_password_opt'],
                         env['db_name'], remote_filename))
                    run('rm %s' % (remote_filename))
            else:
                print('\nAborting.')
        else:
            print('\nERROR: The file "%s" does not exist. Aborting.' % dumpfile)
    else:
        print('\nERROR: A (local) dumpfile must be provided. Aborting.')


def dump_db(dumpfile="pootle_DB_backup.sql"):
    """Dumps the DB as a SQL script and downloads it"""
    require('environment', provided_by=[production, staging])

    if isfile(dumpfile) and confirm('\n%s already exists locally. Do you '
                                    'want to overwrite it?' % dumpfile,
                                    default=False):

        remote_filename = '%s/%s' % (env['project_path'], dumpfile)

        if (not exists(remote_filename) or
            confirm('\n%s already exists. Do you want to overwrite it?'
                    % remote_filename, default=False)):

            print('\nDumping DB...')

            with settings(hide('stderr')):
                run('mysqldump -u %s %s %s > %s' %
                    (env['db_user'], env['db_password_opt'],
                     env['db_name'], remote_filename))
                get(remote_filename, '.')
                run('rm %s' % (remote_filename))
        else:
            print('\nAborting.')
    else:
        print('\nAborting.')


def update_code(branch="master"):
    """Updates the source code and its requirements"""
    require('environment', provided_by=[production, staging])

    print('Getting the latest code and dependencies...')

    with settings(hide('stdout', 'stderr')):
        _checkout_repo(branch=branch)
        _update_requirements()


def deploy_static():
    """Runs `collectstatic` to collect all the static files"""
    require('environment', provided_by=[production, staging])

    print('Collecting and building static files...')

    with settings(hide('stdout', 'stderr')):
        with cd('%(project_repo_path)s' % env):
            with prefix('source %(env_path)s/bin/activate' % env):
                run('mkdir -p pootle/assets')
                run('python manage.py collectstatic --noinput --clear')
                run('python manage.py assets build')
    run('chmod -R go=u,go-w %(project_repo_path)s' % env)


def deploy(branch="master"):
    """Updates the code and installs the production site"""
    require('environment', provided_by=[production, staging])

    print('Deploying the site...')

    with settings(hide('stdout', 'stderr')):
        update_code(branch=branch)
        deploy_static()
        install_site()


def install_site():
    """Configures the server and enables the site"""
    require('environment', provided_by=[production, staging])

    print('Configuring and installing site...')

    with settings(hide('stdout', 'stderr')):
        update_config()
        enable_site()


def update_config():
    """Updates server configuration files"""
    require('environment', provided_by=[production, staging])

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
    print('%s site...' % action)

    env.apache_command = 'a2ensite' if enable else 'a2dissite'
    sudo('%(apache_command)s %(project_name)s' % env)
    sudo('service apache2 reload')


def touch():
    """Reloads daemon processes by touching the WSGI file"""
    require('environment', provided_by=[production, staging])

    print('Running touch...')

    with settings(hide('stdout', 'stderr')):
        run('touch %(wsgi_file)s' % env)


def compile_translations():
    """Compiles PO translations"""
    require('environment', provided_by=[production, staging])

    print('Compiling translations...')

    with settings(hide('stdout', 'stderr')):
        with cd(env.project_repo_path):
            with prefix('source %(env_path)s/bin/activate' % env):
                run('python setup.py build_mo')

def mysql_conf():
    """Sets up .my.cnf file for passwordless MySQL operation"""
    require('environment', provided_by=[production, staging])

    print('Setting up MySQL password configuration...')

    conf_filename = '~/.my.cnf'

    if (not exists(conf_filename) or
        confirm('\n%s already exists. Do you want to overwrite it?'
                % conf_filename, default=False)):

        with settings(hide('stdout', 'stderr')):
            upload_template('deploy/my.cnf' % env, conf_filename, context=env)
            run('chmod 600 %s' % conf_filename)

    else:
        print('\nAborting.')
