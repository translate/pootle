#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
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

from translate.__version__ import build as code_tt_buildversion

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.db import transaction
from django.db.models.signals import post_syncdb, pre_delete, post_delete
from django.utils.translation import ugettext_noop as _

import pootle_app.models
from pootle.__version__ import build as code_buildversion
from pootle_app.models import Directory
from pootle_app.models.permissions import PermissionSet, get_pootle_permission
from pootle_language.models import Language
from pootle_misc import siteconfig
from pootle_profile.models import PootleProfile
from pootle_project.models import Project


def initdb():
    """Populate the database with default initial data.

    This provides a working Pootle installation.
    """

    try:
        # create default cache table
        call_command('createcachetable', 'pootlecache')
    except:
        pass

    create_essential_users()
    create_root_directories()
    create_template_languages()
    create_terminology_project()
    create_pootle_permissions()
    create_pootle_permission_sets()

    create_default_db()

    config = siteconfig.load_site_config()
    if not config.get('POOTLE_BUILDVERSION', None):
        config.set('POOTLE_BUILDVERSION', code_buildversion)
    if not config.get('TT_BUILDVERSION', None):
        config.set('TT_BUILDVERSION', code_tt_buildversion)
    config.save()


def create_default_db():
    """This creates the default database to get a working Pootle installation.

    You can tweak the methods called or their implementation elsewhere in the
    file. This provides some sane default to get things working.
    """
    try:
        transaction.enter_transaction_management()
        transaction.managed(True)

        create_default_projects()
        create_default_languages()
        create_default_admin()
    except:
        if transaction.is_dirty():
            transaction.rollback()
        raise
    finally:
        if transaction.is_managed():
            if transaction.is_dirty():
                transaction.commit()
            transaction.leave_transaction_management()


def create_essential_users():
    """Create the 'default' and 'nobody' User instances.

    These users are required for Pootle's permission system.
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
            'name': _("Can view a translation project"),
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
        permission_set.positive_permissions = [view]
        permission_set.save()

    criteria['profile'] = default
    permission_set, created = PermissionSet.objects.get_or_create(**criteria)
    if created:
        permission_set.positive_permissions = [view]
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
    from pootle_project.models import Project

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
                        'translate.sourceforge.net/wiki/guide/start">'
                        'localisation guide</a>.</div>'),
        'checkstyle': "standard",
        'localfiletype': "po",
        'treestyle': "auto",
    }
    tutorial = Project(**criteria)
    tutorial.save()


def create_default_languages():
    """Create the default languages."""
    from translate.lang import data, factory

    from pootle_language.models import Language

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
