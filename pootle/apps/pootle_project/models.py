#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
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
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.urlresolvers import reverse
from django.db import connection, models
from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.encoding import iri_to_uri
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from translate.filters import checks
from translate.lang.data import langcode_re

from pootle.core.cache import make_method_key
from pootle.core.managers import RelatedManager
from pootle.core.mixins import TreeItem
from pootle.core.models import VirtualResource
from pootle.core.url_helpers import (get_editor_filter, get_path_sortkey,
                                     split_pootle_path)
from pootle_app.models.permissions import PermissionSet
from pootle_store.filetypes import (factory_classes, filetype_choices,
                                    is_monolingual)
from pootle_store.util import absolute_real_path


# FIXME: Generate key dynamically
CACHE_KEY = 'pootle-projects'

RESERVED_PROJECT_CODES = ('admin', 'translate', 'settings')


class ProjectManager(RelatedManager):

    def cached(self):
        projects = cache.get(CACHE_KEY)
        if not projects:
            projects = self.order_by('fullname').all()
            cache.set(CACHE_KEY, projects, settings.OBJECT_CACHE_TIMEOUT)

        return projects

    def enabled(self):
        return self.filter(disabled=False)


class ProjectURLMixin(object):
    """Mixin class providing URL methods to be shared across
    project-related classes.
    """

    def get_absolute_url(self):
        return reverse('pootle-project-overview', args=[self.code, ''])

    def get_translate_url(self, **kwargs):
        lang, proj, dir, fn = split_pootle_path(self.pootle_path)

        if proj is not None:
            pattern_name = 'pootle-project-translate'
            pattern_args = [proj, dir, fn]
        else:
            pattern_name = 'pootle-projects-translate'
            pattern_args = []

        return u''.join([
            reverse(pattern_name, args=pattern_args),
            get_editor_filter(**kwargs),
        ])


class Project(models.Model, TreeItem, ProjectURLMixin):

    code = models.CharField(
        max_length=255,
        null=False,
        unique=True,
        db_index=True,
        verbose_name=_('Code'),
        help_text=_('A short code for the project. This should only contain '
                    'ASCII characters, numbers, and the underscore (_) '
                    'character.'),
    )
    fullname = models.CharField(
        max_length=255,
        null=False,
        verbose_name=_("Full Name"),
    )

    checkers = list(checks.projectcheckers.keys())
    checkers.sort()
    checker_choices = [('standard', 'standard')]
    checker_choices.extend([(checker, checker) for checker in checkers])
    checkstyle = models.CharField(
        max_length=50,
        default='standard',
        null=False,
        choices=checker_choices,
        verbose_name=_('Quality Checks'),
    )

    localfiletype = models.CharField(
        max_length=50,
        default="po",
        choices=filetype_choices,
        verbose_name=_('File Type'),
    )
    treestyle = models.CharField(
        max_length=20,
        default='auto',
        choices=(
            # TODO: check that the None is stored and handled correctly
            ('auto', _('Automatic detection (slower)')),
            ('gnu', _('GNU style: files named by language code')),
            ('nongnu', _('Non-GNU: Each language in its own directory')),
        ),
        verbose_name=_('Project Tree Style'),
    )
    source_language = models.ForeignKey(
        'pootle_language.Language',
        db_index=True,
        verbose_name=_('Source Language'),
    )
    ignoredfiles = models.CharField(
        max_length=255,
        blank=True,
        null=False,
        default="",
        verbose_name=_('Ignore Files'),
    )
    directory = models.OneToOneField(
        'pootle_app.Directory',
        db_index=True,
        editable=False,
    )
    report_email = models.EmailField(
        max_length=254,
        blank=True,
        verbose_name=_("Errors Report Email"),
        help_text=_('An email address where issues with the source text can '
                    'be reported.'),
    )
    screenshot_search_prefix = models.URLField(
        blank=True,
        null=True,
        verbose_name=_('Screenshot Search Prefix'),
    )
    creation_time = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        editable=False,
        null=True,
    )
    disabled = models.BooleanField(verbose_name=_('Disabled'), default=False)

    objects = ProjectManager()

    class Meta:
        ordering = ['code']
        db_table = 'pootle_app_project'

    ############################ Properties ###################################

    @property
    def name(self):
        return self.fullname

    @property
    def pootle_path(self):
        return "/projects/" + self.code + "/"

    @property
    def is_terminology(self):
        """Returns ``True`` if this project is a terminology project."""
        return self.checkstyle == 'terminology'

    @property
    def is_monolingual(self):
        """Return ``True`` if this project is monolingual."""
        return is_monolingual(self.get_file_class())

    ############################ Cached properties ############################

    @cached_property
    def languages(self):
        """Returns a list of active :cls:`~pootle_languages.models.Language`
        objects for this :cls:`~pootle_project.models.Project`.
        """
        from pootle_language.models import Language
        # FIXME: we should better have a way to automatically cache models with
        # built-in invalidation -- did I hear django-cache-machine?
        return Language.objects.filter(Q(translationproject__project=self),
                                       ~Q(code='templates'))

    @cached_property
    def resources(self):
        """Returns a list of :cls:`~pootle_app.models.Directory` and
        :cls:`~pootle_store.models.Store` resource paths available for
        this :cls:`~pootle_project.models.Project` across all languages.
        """
        cache_key = make_method_key(self, 'resources', self.code)

        resources = cache.get(cache_key, None)
        if resources is not None:
            return resources

        logging.debug(u'Cache miss for %s', cache_key)

        resources_path = ''.join(['/%/', self.code, '/%'])

        if connection.vendor == 'mysql':
            sql_query = '''
            SELECT DISTINCT
                REPLACE(pootle_path,
                        CONCAT(SUBSTRING_INDEX(pootle_path, '/', 3), '/'),
                        '')
            FROM (
                SELECT pootle_path
                FROM pootle_store_store
                WHERE pootle_path LIKE %s
              UNION
                SELECT pootle_path FROM pootle_app_directory
                WHERE pootle_path LIKE %s
            ) AS t;
            '''
        elif connection.vendor == 'postgresql':
            sql_query = '''
            SELECT DISTINCT
                REPLACE(pootle_path,
                        ARRAY_TO_STRING((
                                         STRING_TO_ARRAY(pootle_path,'/')
                                        )[1:3], '/')
                        || '/',
                        '')
            FROM (
                SELECT pootle_path
                FROM pootle_store_store
                WHERE pootle_path LIKE %s
              UNION
                SELECT pootle_path FROM pootle_app_directory
                WHERE pootle_path LIKE %s
            ) AS t;
            '''
        elif connection.vendor == 'sqlite':
            # Due to the limitations of SQLite there is no way to do this just
            # using raw SQL.
            from pootle_store.models import Store

            store_objs = Store.objects.extra(
                where=[
                    'pootle_store_store.pootle_path LIKE %s',
                    'pootle_store_store.pootle_path NOT LIKE %s',
                ], params=[resources_path, '/templates/%']
            ).select_related('parent').distinct()

            # Populate with stores and their parent directories, avoiding any
            # duplicates
            resources = []
            for store in store_objs.iterator():
                directory = store.parent
                if (not directory.is_translationproject() and
                    all(directory.path != path for path in resources)):
                    resources.append(directory.path)

                if all(store.path != path for path in resources):
                    resources.append(store.path)

            resources.sort(key=get_path_sortkey)

            cache.set(cache_key, resources, settings.OBJECT_CACHE_TIMEOUT)
            return resources

        cursor = connection.cursor()
        cursor.execute(sql_query, [resources_path, resources_path])

        results = cursor.fetchall()

        # Flatten tuple and sort in a list
        resources = list(reduce(lambda x,y: x+y, results))
        resources.sort(key=get_path_sortkey)

        cache.set(cache_key, resources, settings.OBJECT_CACHE_TIMEOUT)

        return resources

    ############################ Methods ######################################

    @classmethod
    def accessible_by_user(cls, user):
        """Returns a list of project codes accessible by `user`.

        Checks for explicit `view` permissions for `user`, and extends
        them with the `default` (if logged-in) and `nobody` users' `view`
        permissions.

        Negative `hide` permissions are also taken into account and
        they'll forbid project access as far as there's no `view`
        permission set at the same level for the same user.

        :param user: The ``User`` instance to get accessible projects for.
        """
        username = 'nobody' if user.is_anonymous() else user.username
        key = iri_to_uri('projects:accessible:%s' % username)
        user_projects = cache.get(key, None)

        if user_projects is not None:
            return user_projects

        logging.debug(u'Cache miss for %s', key)

        if user.is_anonymous():
            allow_usernames = [username]
            forbid_usernames = [username, 'default']
        else:
            allow_usernames = list(set([username, 'default', 'nobody']))
            forbid_usernames = list(set([username, 'default']))

        # FIXME: use `cls.objects.cached_dict().keys()`, but that needs
        # to use the `LiveProjectManager` first, as it only considers
        # `enabled()` projects
        ALL_PROJECTS = cls.objects.values_list('code', flat=True)

        if user.is_superuser:
            user_projects = ALL_PROJECTS
        else:
            ALL_PROJECTS = set(ALL_PROJECTS)

            # Check root for `view` permissions

            root_permissions = PermissionSet.objects.filter(
                directory__pootle_path='/',
                user__username__in=allow_usernames,
                positive_permissions__codename='view',
            )
            if root_permissions.count():
                user_projects = ALL_PROJECTS
            else:
                user_projects = set()

            # Check specific permissions at the project level

            accessible_projects = cls.objects.filter(
                directory__permission_sets__positive_permissions__codename='view',
                directory__permission_sets__user__username__in=allow_usernames,
            ).values_list('code', flat=True)

            forbidden_projects = cls.objects.filter(
                directory__permission_sets__negative_permissions__codename='hide',
                directory__permission_sets__user__username__in=forbid_usernames,
            ).values_list('code', flat=True)

            allow_projects = set(accessible_projects)
            forbid_projects = set(forbidden_projects) - allow_projects
            user_projects = \
                (user_projects.union(allow_projects)).difference(forbid_projects)

        user_projects = list(user_projects)
        cache.set(key, user_projects, settings.OBJECT_CACHE_TIMEOUT)

        return user_projects

    def __unicode__(self):
        return self.fullname

    def save(self, *args, **kwargs):
        # Create file system directory if needed
        project_path = self.get_real_path()
        if not os.path.exists(project_path):
            os.makedirs(project_path)

        from pootle_app.models.directory import Directory
        self.directory = Directory.objects.projects \
                                          .get_or_make_subdir(self.code)

        super(Project, self).save(*args, **kwargs)

        # FIXME: far from ideal, should cache at the manager level instead
        cache.delete(CACHE_KEY)
        User = get_user_model()
        users_list = User.objects.values_list('username', flat=True)
        cache.delete_many(map(lambda x: 'projects:accessible:%s' % x,
                              users_list))

    def delete(self, *args, **kwargs):
        directory = self.directory

        # Just doing a plain delete will collect all related objects in memory
        # before deleting: translation projects, stores, units, quality checks,
        # pootle_store suggestions, pootle_app suggestions and submissions.
        # This can easily take down a process. If we do a translation project
        # at a time and force garbage collection, things stay much more
        # managable.
        import gc
        gc.collect()
        for tp in self.translationproject_set.iterator():
            tp.delete()
            gc.collect()

        super(Project, self).delete(*args, **kwargs)

        directory.delete()

        # FIXME: far from ideal, should cache at the manager level instead
        cache.delete(CACHE_KEY)
        User = get_user_model()
        users_list = User.objects.values_list('username', flat=True)
        cache.delete_many(map(lambda x: 'projects:accessible:%s' % x,
                              users_list))

    def clean(self):
        if self.code in RESERVED_PROJECT_CODES:
            raise ValidationError(
                _('"%s" cannot be used as a project code' % (self.code,))
            )

    ### TreeItem

    def get_children(self):
        return self.translationproject_set.live()

    def get_cachekey(self):
        return self.directory.pootle_path

    def get_parents(self):
        from pootle_app.models.directory import Directory
        return [Directory.objects.projects]

    ### /TreeItem

    def translated_percentage(self):
        total = self.get_total_wordcount()
        translated = self.get_translated_wordcount()
        max_words = max(total, 1)
        return int(100.0 * translated / max_words)

    def get_real_path(self):
        return absolute_real_path(self.code)

    def is_accessible_by(self, user):
        """Returns `True` if the current project is accessible by
        `user`.
        """
        if user.is_superuser:
            return True

        return self.code in Project.accessible_by_user(user)

    def get_template_filetype(self):
        if self.localfiletype == 'po':
            return 'pot'
        else:
            return self.localfiletype

    def get_file_class(self):
        """Returns the TranslationStore subclass required for parsing
        project files."""
        return factory_classes[self.localfiletype]

    def file_belongs_to_project(self, filename, match_templates=True):
        """Tests if ``filename`` matches project filetype (ie. extension).

        If ``match_templates`` is ``True``, this will also check if the
        file matches the template filetype.
        """
        template_ext = os.path.extsep + self.get_template_filetype()
        return (filename.endswith(os.path.extsep + self.localfiletype)
                or match_templates and filename.endswith(template_ext))

    def _detect_treestyle(self):
        try:
            dirlisting = os.walk(self.get_real_path())
            dirpath, dirnames, filenames = dirlisting.next()

            if not dirnames:
                # No subdirectories
                if filter(self.file_belongs_to_project, filenames):
                    # Translation files found, assume gnu
                    return "gnu"
            else:
                # There are subdirectories
                if filter(lambda dirname: dirname == 'templates' or langcode_re.match(dirname), dirnames):
                    # Found language dirs assume nongnu
                    return "nongnu"
                else:
                    # No language subdirs found, look for any translation file
                    for dirpath, dirnames, filenames in os.walk(self.get_real_path()):
                        if filter(self.file_belongs_to_project, filenames):
                            return "gnu"
        except:
            pass

        # Unsure
        return None

    def get_treestyle(self):
        """Returns the real treestyle, if :attr:`Project.treestyle` is set
        to ``auto`` it checks the project directory and tries to guess
        if it is gnu style or nongnu style.

        We are biased towards nongnu because it makes managing projects
        from the web easier.
        """
        if self.treestyle != "auto":
            return self.treestyle
        else:
            detected = self._detect_treestyle()

            if detected is not None:
                return detected

        # When unsure return nongnu
        return "nongnu"

    def get_template_translationproject(self):
        """Returns the translation project that will be used as a template
        for this project.

        First it tries to retrieve the translation project that has the
        special 'templates' language within this project, otherwise it
        falls back to the source language set for current project.
        """
        try:
            return self.translationproject_set.get(language__code='templates')
        except ObjectDoesNotExist:
            try:
                return self.translationproject_set \
                           .get(language=self.source_language_id)
            except ObjectDoesNotExist:
                pass


class ProjectResource(VirtualResource, ProjectURLMixin):

    ### TreeItem

    def _get_code(self, resource):
        return resource.translation_project.language.code

    ### /TreeItem


class ProjectSet(VirtualResource, ProjectURLMixin):

    ### TreeItem

    def _get_code(self, project):
        return project.code

    ### /TreeItem


@receiver([post_delete, post_save])
def invalidate_resources_cache(sender, instance, **kwargs):
    if instance.__class__.__name__ not in ['Directory', 'Store']:
        return

    # Don't invalidate if the save didn't create new objects
    if (('created' in kwargs and 'raw' in kwargs) and
        (not kwargs['created'] or kwargs['raw'])):
        return

    lang, proj, dir, fn = split_pootle_path(instance.pootle_path)
    if proj is not None:
        cache.delete(make_method_key(Project, 'resources', proj))
