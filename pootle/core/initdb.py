#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

import logging

from translate.__version__ import build as CODE_TTK_BUILD_VERSION
from translate.lang import data, factory

from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.db import transaction
from django.utils.translation import ugettext_noop as _

from pootle.__version__ import build as CODE_PTL_BUILD_VERSION
from pootle_app.models import Directory, PootleConfig
from pootle_app.models.permissions import PermissionSet, get_pootle_permission
from pootle_app.models import PootleSite
from pootle_language.models import Language
from pootle_profile.models import PootleProfile
from pootle_project.models import Project
from pootle_store.models import TMUnit, Unit
from pootle_store.util import TRANSLATED


def initdb():
    """Populate the database with default initial data.

    This creates the default database to get a working Pootle installation.
    """
    create_essential_users()
    create_root_directories()
    create_template_languages()
    create_terminology_project()
    create_pootle_permissions()
    create_pootle_permission_sets()

    create_default_projects()
    create_default_languages()
    create_default_admin()

    create_default_pootle_site(settings.TITLE, settings.DESCRIPTION)

    create_local_tm()

    save_build_versions()


def create_essential_users():
    """Create the 'default', 'nobody' and 'system' User instances.

    The 'default' and 'nobody' users are required for Pootle's permission
    system.

    The 'system' user is required for logging the actions performed by the
    management commands.
    """
    # The nobody user is used to represent an anonymous user in cases where
    # we need to associate model information with such a user. An example is
    # in the permission system: we need a way to store rights for anonymous
    # users; thus we use the nobody user.
    criteria = {
        'username': u"nobody",
        'first_name': u"any anonymous user",
        'is_active': True,
    }
    nobody, created = User.objects.get_or_create(**criteria)
    if created:
        nobody.set_unusable_password()
        nobody.save()

    # The 'default' user represents any valid, non-anonymous user and is used
    # to associate information any such user. An example is in the permission
    # system: we need a way to store default rights for users. We use the
    # 'default' user for this.
    #
    # In a future version of Pootle we should think about using Django's
    # groups to do better permissions handling.
    criteria = {
        'username': u"default",
        'first_name': u"any authenticated user",
        'is_active': True,
    }
    default, created = User.objects.get_or_create(**criteria)
    if created:
        default.set_unusable_password()
        default.save()

    # Now create the 'system' user.
    create_system_user()


def create_system_user():
    """Create the 'system' User instance.

    The 'system' user represents a system, and is used to associate updates
    done by bulk commands as update_stores.
    """
    criteria = {
        'username': u"system",
        'first_name': u"system user",
        'is_active': True,
    }
    system, created = User.objects.get_or_create(**criteria)
    if created:
        system.set_unusable_password()
        system.save()


def create_pootle_permissions():
    """Create Pootle's directory level permissions."""

    args = {
        'app_label': "pootle_app",
        'model': "directory",
    }
    pootle_content_type, created = ContentType.objects.get_or_create(**args)
    pootle_content_type.name = 'pootle'
    pootle_content_type.save()

    # Create the permissions.
    permissions = [
        {
            'name': _("Can view a project"),
            'codename': "view",
        },
        {
            'name': _("Can make a suggestion for a translation"),
            'codename': "suggest",
        },
        {
            'name': _("Can submit a translation"),
            'codename': "translate",
        },
        {
            'name': _("Can overwrite translations on uploading files"),
            'codename': "overwrite",
        },
        {
            'name': _("Can review translations"),
            'codename': "review",
        },
        {
            'name': _("Can download archives of translation projects"),
            'codename': "archive",
        },
        {
            'name': _("Can administrate a translation project"),
            'codename': "administrate",
        },
        {
            'name': _("Can commit to version control"),
            'codename': "commit",
        },
    ]

    criteria = {
        'content_type': pootle_content_type,
    }

    for permission in permissions:
        criteria.update(permission)
        obj, created = Permission.objects.get_or_create(**criteria)


def create_pootle_permission_sets():
    """Create the default permission set for the 'nobody' and 'default' users.

    'nobody' is the anonymous (non-logged in) user, and 'default' is the logged
    in user.
    """
    nobody = PootleProfile.objects.get(user__username='nobody')
    default = PootleProfile.objects.get(user__username='default')

    view = get_pootle_permission('view')
    suggest = get_pootle_permission('suggest')
    translate = get_pootle_permission('translate')
    archive = get_pootle_permission('archive')

    # Default permissions for tree root.
    criteria = {
        'profile': nobody,
        'directory': Directory.objects.root,
    }
    permission_set, created = PermissionSet.objects.get_or_create(**criteria)
    if created:
        permission_set.positive_permissions = [view, suggest]
        permission_set.save()

    criteria['profile'] = default
    permission_set, created = PermissionSet.objects.get_or_create(**criteria)
    if created:
        permission_set.positive_permissions = [view, suggest, translate,
                                               archive]
        permission_set.save()

    # Default permissions for templates language.
    # Override with no permissions for templates language.
    criteria = {
        'profile': nobody,
        'directory': Directory.objects.get(pootle_path="/templates/"),
    }
    permission_set, created = PermissionSet.objects.get_or_create(**criteria)
    if created:
        permission_set.positive_permissions = []
        permission_set.save()

    criteria['profile'] = default
    permission_set, created = PermissionSet.objects.get_or_create(**criteria)
    if created:
        permission_set.positive_permissions = []
        permission_set.save()


def require_english():
    """Create the English Language item."""
    criteria = {
        'code': "en",
        'fullname': u"English",
        'nplurals': 2,
        'pluralequation': "(n != 1)",
    }
    en, created = Language.objects.get_or_create(**criteria)
    return en


def create_root_directories():
    """Create the root Directory items."""
    root, created = Directory.objects.get_or_create(name='')
    projects, created = Directory.objects.get_or_create(name='projects',
                                                        parent=root)
    goals, created = Directory.objects.get_or_create(name='goals', parent=root)


def create_template_languages():
    """Create the 'templates' and English languages.

    The 'templates' language is used to give users access to the untranslated
    template files.
    """
    templates, created = Language.objects.get_or_create(code="templates",
                                                        fullname=u'Templates')
    require_english()


def create_terminology_project():
    """Create the terminology project.

    The terminology project is used to display terminology suggestions while
    translating.
    """
    criteria = {
        'code': "terminology",
        'fullname': u"Terminology",
        'source_language': require_english(),
        'checkstyle': "terminology",
    }
    terminology, created = Project.objects.get_or_create(**criteria)


def create_default_projects():
    """Create the default projects that we host.

    You might want to add your projects here, although you can also add things
    through the web interface later.
    """
    en = require_english()

    #criteria = {
    #    'code': u"pootle",
    #    'source_language': en,
    #    'fullname': u"Pootle",
    #    'description': ('<div dir="ltr" lang="en">Interface translations for '
    #                    'Pootle.<br />See the <a href="http://'
    #                    'pootle.locamotion.org">official Pootle server</a> '
    #                    'for the translations of Pootle.</div>')
    #    'checkstyle': "standard",
    #    'localfiletype': "po",
    #    'treestyle': "auto",
    #}
    #pootle = Project(**criteria)
    #pootle.save()

    criteria = {
        'code': u"tutorial",
        'source_language': en,
        'fullname': u"Tutorial",
        'description': ('<div dir="ltr" lang="en">Tutorial project where '
                        'users can play with Pootle and learn more about '
                        'translation and localisation.<br />For more help on '
                        'localisation, visit the <a href="http://'
                        'docs.translatehouse.org/projects/localization-guide/'
                        'en/latest/guide/start.html">localisation guide</a>.'
                        '</div>'),
        'checkstyle': "standard",
        'localfiletype': "po",
        'treestyle': "auto",
    }
    tutorial = Project(**criteria)
    tutorial.save()


def create_default_languages():
    """Create the default languages."""

    # Import languages from toolkit.
    for code in data.languages.keys():
        try:
            tk_lang = factory.getlanguage(code)
            criteria = {
                'code': code,
                'fullname': tk_lang.fullname,
                'nplurals': tk_lang.nplurals,
                'pluralequation': tk_lang.pluralequation,
            }
            try:
                criteria['specialchars'] = tk_lang.specialchars
            except AttributeError:
                pass
            lang, created = Language.objects.get_or_create(**criteria)
        except:
            pass


def create_default_admin():
    """Create the default admin user for Pootle.

    You definitely want to change the admin account so that your default
    install is not accessible with the default credentials. The users 'noboby'
    and 'default' should be left as is.
    """
    criteria = {
        'username': u"admin",
        'first_name': u"Administrator",
        'is_active': True,
        'is_superuser': True,
        'is_staff': True,
    }
    admin = User(**criteria)
    admin.set_password("admin")
    admin.save()


def create_default_pootle_site(site_title, site_description):
    """Create a PootleSite object to store the site title and description."""
    # Get or create a Site object.
    site, created = Site.objects.get_or_create(pk=settings.SITE_ID)
    if created:
        # FIXME: If possible try to retrieve the domain and name from settings.
        site.domain = u"example.com"
        site.name = u"example.com"
        site.save()

    # Create the PootleSite object.
    pootle_site = PootleSite(
        site=site,
        title=site_title,
        description=site_description,
    )
    pootle_site.save()


def create_local_tm():
    """Create the local TM using translations from existing projects.

    Iterates over all the translation units and creates the corresponding local
    TM units.
    """
    logging.info('About to create local TM using existing translations')

    with transaction.commit_on_success():
        for unit in Unit.objects.filter(state__gte=TRANSLATED).iterator():
            tmunit = TMUnit().create(unit)
            tmunit.save()

        logging.info('Successfully created local TM from existing translations')


def save_build_versions():
    """Save the Pootle and Translate Toolkit build versions on the database.

    The build versions are used to upgrade only what has to be upgraded.
    """
    pootle_config = PootleConfig(
        ptl_build=CODE_PTL_BUILD_VERSION,
        ttk_build=CODE_TTK_BUILD_VERSION
    )
    pootle_config.save()
