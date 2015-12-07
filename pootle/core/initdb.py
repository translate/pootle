#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import re
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_noop as _

from pootle.core.models import Revision
from pootle_app.models import Directory
from pootle_app.models.permissions import PermissionSet, get_pootle_permission
from pootle_language.models import Language
from pootle_project.models import Project
from staticpages.models import StaticPage as Announcement


logger = logging.getLogger(__name__)
re_plurals = re.compile(r'nplurals=(\d); plural=(.+)$')


CLDR_FALLBACK_ALIASES = {
    # new name: list of fallback names
    'zh_Hans': ['zh_CN'],
    'zh_Hant': ['zh_TW', 'zh_HK'],
}


class InitDB(object):

    def init_db(self, create_projects=True, cldr=False):
        """Populate the database with default initial data.

        This creates the default database to get a working Pootle installation.
        """
        self.create_revision()
        self.create_essential_users()
        self.create_root_directories()
        self.create_template_languages()
        if create_projects:
            self.create_terminology_project()
        self.create_pootle_permissions()
        self.create_pootle_permission_sets()
        if create_projects:
            self.create_default_projects()
        if cldr:
            self.create_default_languages_cldr()
        else:
            self.create_default_languages()

    def _create_object(self, model_klass, **criteria):
        instance, created = model_klass.objects.get_or_create(**criteria)
        if created:
            logger.debug(
                "Created %s: '%s'"
                % (instance.__class__.__name__, instance))
        else:
            logger.debug(
                "%s already exists - skipping: '%s'"
                % (instance.__class__.__name__, instance))
        return instance, created

    def _create_pootle_user(self, **criteria):
        user, created = self._create_object(get_user_model(), **criteria)
        if created:
            user.set_unusable_password()
            user.save()
        return user

    def _create_pootle_permission_set(self, permissions, **criteria):
        permission_set, created = self._create_object(PermissionSet,
                                                      **criteria)
        if created:
            permission_set.positive_permissions = permissions
            permission_set.save()
        return permission_set

    def create_revision(self):
        Revision.initialize()

    def create_essential_users(self):
        """Create the 'default' and 'nobody' User instances.

        These users are required for Pootle's permission system.
        """
        # The nobody user is used to represent an anonymous user in cases
        # where we need to associate model information with such a user. An
        # example is in the permission system: we need a way to store rights
        # for anonymous users; thus we use the nobody user.
        criteria = {
            'username': u"nobody",
            'full_name': u"any anonymous user",
            'is_active': True,
        }
        self._create_pootle_user(**criteria)

        # The 'default' user represents any valid, non-anonymous user and is
        # used to associate information any such user. An example is in the
        # permission system: we need a way to store default rights for users.
        # We use the 'default' user for this.
        #
        # In a future version of Pootle we should think about using Django's
        # groups to do better permissions handling.
        criteria = {
            'username': u"default",
            'full_name': u"any authenticated user",
            'is_active': True,
        }
        self._create_pootle_user(**criteria)

        # The system user represents a system, and is used to
        # associate updates done by bulk commands as update_stores.
        criteria = {
            'username': u"system",
            'full_name': u"system user",
            'is_active': True,
        }
        self._create_pootle_user(**criteria)

    def create_pootle_permissions(self):
        """Create Pootle's directory level permissions."""

        args = {
            'app_label': "pootle_app",
            'model': "directory",
        }

        pootle_content_type, created = self._create_object(ContentType, **args)
        pootle_content_type.name = 'pootle'
        pootle_content_type.save()

        # Create the permissions.
        permissions = [
            {
                'name': _("Can access a project"),
                'codename': "view",
            },
            {
                'name': _("Cannot access a project"),
                'codename': "hide",
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
                'name': _("Can review suggestions"),
                'codename': "review",
            },
            {
                'name': _("Can administrate a translation project"),
                'codename': "administrate",
            },
        ]

        criteria = {
            'content_type': pootle_content_type,
        }

        for permission in permissions:
            criteria.update(permission)
            self._create_object(Permission, **criteria)

    def create_pootle_permission_sets(self):
        """Create the default permission set for the 'nobody' and 'default' users.

        'nobody' is the anonymous (non-logged in) user, and 'default' is the
        logged in user.
        """
        User = get_user_model()

        nobody = User.objects.get(username='nobody')
        default = User.objects.get(username='default')

        view = get_pootle_permission('view')
        suggest = get_pootle_permission('suggest')
        translate = get_pootle_permission('translate')

        # Default permissions for tree root.
        criteria = {
            'user': nobody,
            'directory': Directory.objects.root,
        }
        self._create_pootle_permission_set([view, suggest], **criteria)

        criteria['user'] = default
        self._create_pootle_permission_set(
            [view, suggest, translate], **criteria)

        # Default permissions for templates language.
        # Override with no permissions for templates language.
        criteria = {
            'user': nobody,
            'directory': Directory.objects.get(pootle_path="/templates/"),
        }
        self._create_pootle_permission_set([], **criteria)

        criteria['user'] = default
        self._create_pootle_permission_set([], **criteria)

    def require_english(self):
        """Create the English Language item."""
        criteria = {
            'fullname': u"English",
            'nplurals': 2,
            'pluralequation': "(n != 1)",
        }
        en, created = self._create_object(Language, code='en', defaults=criteria)
        return en

    def create_root_directories(self):
        """Create the root Directory items."""
        root, created = self._create_object(Directory, **dict(name=""))
        self._create_object(Directory, **dict(name="projects", parent=root))

    def create_template_languages(self):
        """Create the 'templates' and English languages.

        The 'templates' language is used to give users access to the
        untranslated template files.
        """
        self._create_object(
            Language, code='templates', defaults=dict(fullname="Templates"))
        self.require_english()

    def create_terminology_project(self):
        """Create the terminology project.

        The terminology project is used to display terminology suggestions
        while translating.
        """
        criteria = {
            'code': "terminology",
            'fullname': u"Terminology",
            'source_language': self.require_english(),
            'checkstyle': "terminology",
        }
        self._create_object(Project, **criteria)

    def create_default_projects(self):
        """Create the default projects that we host.

        You might want to add your projects here, although you can also add
        things through the web interface later.
        """
        from pootle_project.models import Project

        en = self.require_english()

        criteria = {
            'code': u"tutorial",
            'source_language': en,
            'fullname': u"Tutorial",
            'checkstyle': "standard",
            'localfiletype': "po",
            'treestyle': "auto",
        }
        tutorial, created = self._create_object(Project, **criteria)

        criteria = {
            'active': True,
            'title': "Project instructions",
            'body': (
                '<div dir="ltr" lang="en">Tutorial project where users can '
                'play with Pootle and learn more about translation and '
                'localisation.<br />For more help on localisation, visit the '
                '<a href="http://docs.translatehouse.org/projects/'
                'localization-guide/en/latest/guide/start.html">localisation '
                'guide</a>.</div>'),
            'virtual_path': "announcements/projects/"+tutorial.code,
        }
        self._create_object(Announcement, **criteria)

    def create_default_languages(self):
        """Create the default languages."""
        from translate.lang import data, factory

        from pootle_language.models import Language

        # import languages from toolkit
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
                self._create_object(Language, **criteria)
            except:
                pass

    def create_default_languages_cldr(self):
        """
        Generate Language objects from CLDR database

        You can optionally set up a list of 'fallback aliases' (mappings from language definitions existing in CLDR
        to locale names which you need in your Pootle installation)
        """
        from pootle_language.models import Language
        for attrs in self.get_cldr_languages():
            code = attrs.pop('code')
            self._create_object(Language, code=code, defaults=attrs)

    def get_cldr_languages(self):
        """
        Helper function to extract CLDR information. Heavily relied on babel functionality
        """
        from babel import Locale, localedata, plural

        for lang in localedata.locale_identifiers():
            locale = Locale(lang)
            if not locale.english_name:
                continue

            plurals_str = plural.to_gettext(locale.plural_form)
            nplurals, pluralequation = re_plurals.match(plurals_str).groups()
            lang_aliases = set(CLDR_FALLBACK_ALIASES.get(lang, []))
            lang_aliases.add(lang)
            for alias in lang_aliases:
                yield {
                    'code': alias,
                    'fullname': locale.english_name,
                    'nplurals': int(nplurals),
                    'pluralequation': pluralequation,
                }
