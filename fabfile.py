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

from fabric.api import cd, env
from fabric.context_managers import hide, prefix, settings
from fabric.contrib.console import confirm
from fabric.contrib.files import exists, upload_template
from fabric.operations import require, run, sudo

#
# Deployment environments
#

def production():
    """Work on the production environment"""
    from deploy.production import fabric
    env.update(fabric.SETTINGS)
    env.environment = 'production'


def staging():
    """Work on the staging environment"""
    from deploy.staging import fabric
    env.update(fabric.SETTINGS)
    env.environment = 'staging'


#
# Commands
#

def _init_directories():
    """Creates initial directories"""
    if exists('%(project_path)s' % env):
        sudo('rm -rf %(project_path)s' % env)

    sudo('mkdir -p %(project_path)s' % env)
    sudo('chown %(user)s:%(server_group)s %(project_path)s' % env)
    run('mkdir -m g+w %(project_path)s/logs' % env)


def _init_virtualenv():
    """Creates initial virtualenv"""
    run('virtualenv -p %(python)s --no-site-packages %(env_path)s' % env)
    with prefix('source %(env_path)s/bin/activate' % env):
        run('easy_install pip' % env)


def _clone_repo():
    """Clones the git repository"""
    run('git clone %(project_repo)s %(project_repo_path)s' % env)


# TODO: Accept branches other than the default
def _checkout_repo():
    """Updates the git repository"""
    with cd(env.project_repo_path):
        run('git pull')


def _install_requirements():
    """Installs dependencies defined in the requirements file"""
    with prefix('source %(env_path)s/bin/activate' % env):
        run('pip install -r %(project_repo_path)s/requirements/deploy.txt' % env)


def _update_requirements():
    """Updates dependencies installed via pip"""
    with prefix('source %(env_path)s/bin/activate' % env):
        run('pip freeze --local | awk \'BEGIN{FS="=="}{print $1}\' | '
            'xargs pip install -U' % env)


def bootstrap():
    """Creates initial directories and virtualenv"""
    require('environment', provided_by=[production, staging])

    if (exists('%(project_path)s' % env) and \
        confirm('%(project_path)s already exists. Do you want to continue?' \
                % env, default=False)) or not exists('%(project_path)s' % env):

            print('Bootstrapping initial directories...')

            with settings(hide('stdout', 'stderr')):
                _init_directories()
                _init_virtualenv()
                _clone_repo()
                _checkout_repo()
                _install_requirements()
    else:
        print('Aborting.')


def update_db():
    """Updates database schemas"""
    require('environment', provided_by=[production, staging])

    with settings(hide('stdout', 'stderr')):
        with cd('%(project_repo_path)s/pootle' % env):
            with prefix('source %(env_path)s/bin/activate' % env):
                run('python manage.py updatedb')


def update_code():
    """Updates the source code and its requirements"""
    require('environment', provided_by=[production, staging])

    print('Getting the latest code and dependencies...')

    with settings(hide('stdout', 'stderr')):
        _checkout_repo()
        _update_requirements()


def deploy_static():
    """Runs `collectstatic` to collect all the static files"""
    require('environment', provided_by=[production, staging])

    print('Collecting and building static files...')

    with settings(hide('stdout', 'stderr')):
        with cd('%(project_repo_path)s/pootle' % env):
            with prefix('source %(env_path)s/bin/activate' % env):
                run('python manage.py collectstatic --noinput')
                run('python manage.py assets build')


def deploy():
    """Updates the code and installs the production site"""
    require('environment', provided_by=[production, staging])

    print('Deploying the site...')

    with settings(hide('stdout', 'stderr')):
        update_code()
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
                        '%(project_settings_path)s/90-%(environment)s-local.conf' \
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
