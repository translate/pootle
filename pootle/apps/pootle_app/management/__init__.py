#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import logging

from django.db.models.signals import post_syncdb, pre_delete, post_delete
from django.utils.translation import ugettext_noop as _
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command

import pootle_app.models
from pootle_app.models import Directory
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_profile.models import PootleProfile
from pootle_app.models.permissions import PermissionSet, get_pootle_permission
from pootle_misc import siteconfig

from pootle.__version__ import build as code_buildversion
from translate.__version__ import build as code_tt_buildversion

def create_essential_users():
    """Create default and nobody User instances required for pootle permission system"""
    # The nobody user is used to represent an anonymous user in cases where
    # we need to associate model information with such a user. An example is
    # in the permission system: we need a way to store rights for anonymous
    # users; thus we use the nobody user.
    nobody, created = User.objects.get_or_create(username=u"nobody",
                first_name=u"any anonymous user",
                is_active=True)
    if created:
        nobody.set_unusable_password()
        nobody.save()

    # The default user represents any valid, non-anonymous user and is used to
    # associate information any such user. An example is in the permission
    # system: we need a way to store default rights for users. We use the
    # default user for this.
    #
    # In a future version of Pootle we should think about using Django's
    # groups to do better permissions handling.
    default, created = User.objects.get_or_create(username=u"default",
                 first_name=u"any authenticated user",
                 is_active=True)
    if created:
        default.set_unusable_password()
        default.save()

def create_pootle_permissions():
    """define Pootle's directory level permissions"""
    pootle_content_type, created = ContentType.objects.get_or_create(app_label="pootle_app", model="directory")
    pootle_content_type.name = 'pootle'
    pootle_content_type.save()
    view, created = Permission.objects.get_or_create(name=_("Can view a translation project"),
                                                     content_type=pootle_content_type, codename="view")
    suggest, created = Permission.objects.get_or_create(name=_("Can make a suggestion for a translation"),
                                               content_type=pootle_content_type, codename="suggest")
    translate, created = Permission.objects.get_or_create(name=_("Can submit a translation"),
                                                 content_type=pootle_content_type, codename="translate")
    overwrite, created = Permission.objects.get_or_create(name=_("Can overwrite translations on uploading files"),
                                                 content_type=pootle_content_type, codename="overwrite")
    review, created = Permission.objects.get_or_create(name=_("Can review translations"),
                                                       content_type=pootle_content_type, codename="review")
    archive, created = Permission.objects.get_or_create(name=_("Can download archives of translation projects"),
                                                        content_type=pootle_content_type, codename="archive")
    administrate, created = Permission.objects.get_or_create(name=_("Can administrate a translation project"),
                                                    content_type=pootle_content_type, codename="administrate")
    commit, created = Permission.objects.get_or_create(name=_("Can commit to version control"),
                                                       content_type=pootle_content_type, codename="commit")

def create_pootle_permission_sets():
    """Create the default permission set for the anonymous (non-logged in) user
    ('nobody') and for the logged in user ('default')."""
    nobody = PootleProfile.objects.get(user__username='nobody')
    default = PootleProfile.objects.get(user__username='default')

    view = get_pootle_permission('view')
    suggest = get_pootle_permission('suggest')
    translate = get_pootle_permission('translate')
    archive = get_pootle_permission('archive')

    # Default permissions for tree root
    root = Directory.objects.root
    permission_set, created = PermissionSet.objects.get_or_create(profile=nobody, directory=root)
    if created:
        permission_set.positive_permissions = [view, suggest]
        permission_set.save()

    permission_set, created = PermissionSet.objects.get_or_create(profile=default, directory=root)
    if created:
        permission_set.positive_permissions = [view, suggest, translate, archive]
        permission_set.save()

    # Default permissions for templates language
    templates = Directory.objects.get(pootle_path="/templates/")

    #override with no permissions for templates language
    permission_set, created = PermissionSet.objects.get_or_create(profile=nobody, directory=templates)
    if created:
        permission_set.positive_permissions = [view]
        permission_set.save()

    permission_set, created = PermissionSet.objects.get_or_create(profile=default, directory=templates)
    if created:
        permission_set.positive_permissions = [view]
        permission_set.save()

def require_english():
    en, created = Language.objects.get_or_create(code="en", fullname=u"English",
                                                 nplurals=2, pluralequation="(n != 1)")
    return en

def create_root_directory():
    """Create root Directory item."""
    root, created = Directory.objects.get_or_create(name='')
    projects, created = Directory.objects.get_or_create(name='projects', parent=root)

def create_template_language():
    """template language is used to give users access to the untranslated template files"""
    templates, created = Language.objects.get_or_create(code="templates", fullname=u'Templates')
    require_english()


def create_terminology_project():
    """terminology project is used to display terminology suggestions while translating"""
    en = require_english()
    terminology, created = Project.objects.get_or_create(
            code="terminology",
            fullname=u"Terminology",
            source_language=en,
            checkstyle="terminology",
    )

def post_syncdb_handler(sender, created_models, **kwargs):
    try:
        # create default cache table
        call_command('createcachetable', 'pootlecache')
    except:
        pass

    if PootleProfile in created_models:
        create_essential_users()
    if Directory in created_models:
        create_root_directory()
    if Language in created_models:
        create_template_language()
    if Project in created_models:
        create_terminology_project()
    if PermissionSet in created_models:
        create_pootle_permissions()
        create_pootle_permission_sets()

    config = siteconfig.load_site_config()
    if not config.get('BUILDVERSION', None):
        config.set('BUILDVERSION', code_buildversion)
    if not config.get('TT_BUILDVERSION', None):
        config.set('TT_BUILDVERSION', code_tt_buildversion)
    config.save()
post_syncdb.connect(post_syncdb_handler, sender=pootle_app.models)

permission_queryset = None
def fix_permission_content_type_pre(sender, instance, **kwargs):
    if instance.name == 'pootle' and instance.model == "":
        logging.debug("Fixing permissions content types")
        global permission_queryset
        permission_queryset = [permission for permission in Permission.objects.filter(content_type=instance)]
pre_delete.connect(fix_permission_content_type_pre, sender=ContentType)

def fix_permission_content_type_post(sender, instance, **kwargs):
    global permission_queryset
    if permission_queryset is not None:
        dir_content_type = ContentType.objects.get(app_label='pootle_app', model='directory')
        dir_content_type.name = 'pootle'
        dir_content_type.save()
        for permission in permission_queryset:
            permission.content_type = dir_content_type
            permission.save()
        permission_queryset = None
post_delete.connect(fix_permission_content_type_post, sender=ContentType)
