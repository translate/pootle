# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import shutil
from collections import OrderedDict

from translate.filters import checks
from translate.lang.data import langcode_re

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.encoding import iri_to_uri
from django.utils.functional import cached_property

from sortedm2m.fields import SortedManyToManyField

from pootle.core.cache import make_method_key
from pootle.core.delegate import data_tool, filetype_tool, lang_mapper, tp_tool
from pootle.core.mixins import CachedTreeItem
from pootle.core.models import VirtualResource
from pootle.core.url_helpers import get_editor_filter, split_pootle_path
from pootle.i18n.gettext import ugettext_lazy as _
from pootle_app.models.directory import Directory
from pootle_app.models.permissions import PermissionSet
from pootle_config.utils import ObjectConfig
from pootle_format.models import Format
from pootle_format.utils import ProjectFiletypes
from pootle_revision.models import Revision
from pootle_store.util import absolute_real_path
from staticpages.models import StaticPage


RESERVED_PROJECT_CODES = ('admin', 'translate', 'settings')
PROJECT_CHECKERS = {
    "standard": checks.StandardChecker,
    "minimal": checks.MinimalChecker,
    "reduced": checks.ReducedChecker,
    "openoffice": checks.OpenOfficeChecker,
    "libreoffice": checks.LibreOfficeChecker,
    "mozilla": checks.MozillaChecker,
    "kde": checks.KdeChecker,
    "wx": checks.KdeChecker,
    "gnome": checks.GnomeChecker,
    "creativecommons": checks.CCLicenseChecker,
    "drupal": checks.DrupalChecker,
    "terminology": checks.TermChecker,
    "l20n": checks.L20nChecker,
}


class ProjectManager(models.Manager):

    def create(self, *args, **kwargs):
        filetypes = Format.objects.filter(name__in=kwargs.pop("filetypes", ["po"]))
        project = super(ProjectManager, self).create(*args, **kwargs)
        for filetype in filetypes:
            project.filetypes.add(filetype)
        return project

    def get_or_create(self, *args, **kwargs):
        project, created = super(
            ProjectManager, self).get_or_create(*args, **kwargs)
        if created and not project.filetypes.count():
            project.filetypes.add(Format.objects.get(name="po"))
        return project, created

    def cached_dict(self, user):
        """Return a cached ordered dictionary of projects tuples for `user`.

        - Admins always get all projects.
        - Regular users only get enabled projects accessible to them.

        :param user: The user for whom projects need to be retrieved for.
        :return: An ordered dictionary of project tuples including
          (`fullname`, `disabled`) and `code` is a key in the dictionary.
        """
        if not user.is_superuser:
            cache_params = {'username': user.username}
        else:
            cache_params = {'is_admin': user.is_superuser}
        cache_key = iri_to_uri(make_method_key('Project', 'cached_dict',
                                               cache_params))
        projects = cache.get(cache_key)
        if not projects:
            projects_dict = self.for_user(user).order_by('fullname') \
                                               .values('code', 'fullname',
                                                       'disabled')

            projects = OrderedDict(
                (project.pop('code'), project) for project in projects_dict
            )
            cache.set(cache_key, projects, settings.POOTLE_CACHE_TIMEOUT)

        return projects

    def enabled(self):
        return self.filter(disabled=False)

    def get_for_user(self, project_code, user):
        """Gets a `project_code` project for a specific `user`.

        - Admins can get the project even if it's disabled.
        - Regular users only get a project if it's not disabled and
            it is accessible to them.

        :param project_code: The code of the project to retrieve.
        :param user: The user for whom the project needs to be retrieved.
        :return: The `Project` matching the params, raises otherwise.
        """
        if user.is_superuser:
            return self.get(code=project_code)

        return self.for_user(user).get(code=project_code)

    def for_user(self, user):
        """Filters projects for a specific user.

        - Admins always get all projects.
        - Regular users only get enabled projects accessible to them.

        :param user: The user for whom the projects need to be retrieved for.
        :return: A filtered queryset with `Project`s for `user`.
        """
        if user.is_superuser:
            return self.all()

        return self.enabled().filter(code__in=Project.accessible_by_user(user))


class ProjectURLMixin(object):
    """Mixin class providing URL methods to be shared across
    project-related classes.
    """

    def get_absolute_url(self):
        proj_code = split_pootle_path(self.pootle_path)[1]

        if proj_code is not None:
            pattern_name = 'pootle-project-browse'
            pattern_args = [proj_code, '']
        else:
            pattern_name = 'pootle-projects-browse'
            pattern_args = []

        return reverse(pattern_name, args=pattern_args)

    def get_translate_url(self, **kwargs):
        proj_code, dir_path, filename = split_pootle_path(self.pootle_path)[1:]

        if proj_code is not None:
            pattern_name = 'pootle-project-translate'
            pattern_args = [proj_code, dir_path, filename]
        else:
            pattern_name = 'pootle-projects-translate'
            pattern_args = []

        return u''.join([
            reverse(pattern_name, args=pattern_args),
            get_editor_filter(**kwargs),
        ])


def validate_not_reserved(value):
    if value in RESERVED_PROJECT_CODES:
        raise ValidationError(
            _('"%(code)s" cannot be used as a project code'),
            params={'code': value},
        )


def validate_project_checker(value):
    if value not in PROJECT_CHECKERS.keys():
        raise ValidationError(
            # Translators: this refers to the project quality checker
            _('"%(code)s" cannot be used as a project checker'),
            params={'code': value},
        )


class Project(models.Model, CachedTreeItem, ProjectURLMixin):

    code_help_text = _('A short code for the project. This should only '
                       'contain ASCII characters, numbers, and the underscore '
                       '(_) character.')
    # any changes to the `code` field may require updating the schema
    # see migration 0003_case_sensitive_schema.py
    code = models.CharField(max_length=255, null=False, unique=True,
                            db_index=True, verbose_name=_('Code'), blank=False,
                            validators=[validate_not_reserved],
                            help_text=code_help_text)

    fullname = models.CharField(max_length=255, null=False, blank=False,
                                verbose_name=_("Full Name"))

    checkstyle = models.CharField(
        max_length=50,
        default='standard',
        null=False,
        validators=[validate_project_checker],
        verbose_name=_('Quality Checks'))

    filetypes = SortedManyToManyField(Format)

    treestyle_choices = (
        # TODO: check that the None is stored and handled correctly
        ('auto', _('Automatic detection of GNU/non-GNU file layouts (slower)')),
        ('gnu', _('GNU style: files named by language code')),
        ('nongnu', _('Non-GNU: Each language in its own directory')),
        ('pootle_fs', _('Allow Pootle FS to manage filesystems (Experimental)')),
    )
    treestyle = models.CharField(max_length=20, default='auto',
                                 choices=treestyle_choices,
                                 verbose_name=_('Project Tree Style'))

    source_language = models.ForeignKey(
        'pootle_language.Language', db_index=True,
        verbose_name=_('Source Language'), on_delete=models.CASCADE)

    ignoredfiles = models.CharField(
        max_length=255, blank=True, null=False, default="",
        verbose_name=_('Ignore Files'))

    directory = models.OneToOneField(
        'pootle_app.Directory', db_index=True, editable=False,
        on_delete=models.CASCADE)
    report_email = models.EmailField(
        max_length=254, blank=True, verbose_name=_("Errors Report Email"),
        help_text=_('An email address where issues with the source text '
                    'can be reported.'))

    screenshot_search_prefix = models.URLField(
        # Translators: This is the URL prefix to search for context screenshots
        blank=True, null=True, verbose_name=_('Screenshot Search Prefix'))

    creation_time = models.DateTimeField(auto_now_add=True, db_index=True,
                                         editable=False, null=True)

    disabled = models.BooleanField(verbose_name=_('Disabled'), default=False)
    revisions = GenericRelation(Revision)

    objects = ProjectManager()

    class Meta(object):
        ordering = ['code']
        db_table = 'pootle_app_project'

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
        if user.is_superuser:
            key = iri_to_uri('projects:all')
        else:
            username = user.username
            key = iri_to_uri('projects:accessible:%s' % username)
        user_projects = cache.get(key, None)

        if user_projects is not None:
            return user_projects

        # FIXME: use `cls.objects.cached_dict().keys()`
        ALL_PROJECTS = cls.objects.values_list('code', flat=True)

        if user.is_superuser:
            user_projects = ALL_PROJECTS
        else:
            ALL_PROJECTS = set(ALL_PROJECTS)

            if user.is_anonymous:
                allow_usernames = [username]
                forbid_usernames = [username, 'default']
            else:
                allow_usernames = list(set([username, 'default', 'nobody']))
                forbid_usernames = list(set([username, 'default']))

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
            user_projects = (user_projects.union(
                allow_projects)).difference(forbid_projects)

        user_projects = list(user_projects)
        cache.set(key, user_projects, settings.POOTLE_CACHE_TIMEOUT)

        return user_projects

    @cached_property
    def data_tool(self):
        return data_tool.get(self.__class__)(self)

    # # # # # # # # # # # # # #  Properties # # # # # # # # # # # # # # # # # #

    @cached_property
    def config(self):
        return ObjectConfig(self)

    @cached_property
    def filetype_tool(self):
        return filetype_tool.get(self.__class__)(self)

    @cached_property
    def lang_mapper(self):
        return lang_mapper.get(self.__class__, instance=self)

    @cached_property
    def tp_tool(self):
        return tp_tool.get(self.__class__)(self)

    @property
    def local_fs_path(self):
        return os.path.join(settings.POOTLE_FS_WORKING_PATH, self.code)

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

    # # # # # # # # # # # # # #  Methods # # # # # # # # # # # # # # # # # # #

    def __unicode__(self):
        return self.fullname

    def save(self, *args, **kwargs):
        self.fullname = self.fullname.strip()
        self.code = self.code.strip()

        # Force validation of fields.
        self.full_clean()

        requires_translation_directory = (
            self.treestyle != 'pootle_fs'
            and not self.disabled
            and not self.directory_exists_on_disk())
        if requires_translation_directory:
            os.makedirs(self.get_real_path())

        self.directory = Directory.objects.projects \
                                          .get_or_make_subdir(self.code)

        super(Project, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if os.path.exists(self.local_fs_path):
            shutil.rmtree(self.local_fs_path)

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

    def directory_exists_on_disk(self):
        """Checks if the actual directory for the project exists on disk."""
        return os.path.exists(self.get_real_path())

    # # # TreeItem

    def get_children(self):
        return self.translationproject_set.live()

    # # # /TreeItem

    def get_children_for_user(self, user, select_related=None):
        """Returns children translation projects for a specific `user`."""
        return (
            self.translationproject_set.for_user(user, select_related)
                                       .select_related("language"))

    def get_announcement(self, user=None):
        """Return the related announcement, if any."""
        return StaticPage.get_announcement_for(self.pootle_path, user)

    def get_real_path(self):
        return absolute_real_path(self.code)

    def is_accessible_by(self, user):
        """Returns `True` if the current project is accessible by
        `user`.
        """
        if user.is_superuser:
            return True

        return self.code in Project.accessible_by_user(user)

    def file_belongs_to_project(self, filename, match_templates=True):
        """Tests if ``filename`` matches project filetype (ie. extension).

        If ``match_templates`` is ``True``, this will also check if the file
        matches the template filetype.
        """
        ext = os.path.splitext(filename)[1][1:]
        filetypes = ProjectFiletypes(self)
        return (
            ext in filetypes.filetype_extensions
            or (match_templates
                and ext in filetypes.template_extensions))

    def _detect_treestyle(self):
        try:
            dirlisting = os.walk(self.get_real_path())
            dirpath_, dirnames, filenames = dirlisting.next()

            if not dirnames:
                # No subdirectories
                if filter(self.file_belongs_to_project, filenames):
                    # Translation files found, assume gnu
                    return "gnu"

            # There are subdirectories
            if filter(lambda dirname: dirname == 'templates' or
                      langcode_re.match(dirname), dirnames):
                # Found language dirs assume nongnu
                return "nongnu"

            # No language subdirs found, look for any translation file
            for dirpath_, dirnames, filenames in os.walk(self.get_real_path()):
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

    def __eq__(self, other):
        return (
            self.pootle_path == other.pootle_path
            and list(self.get_children()) == list(other.get_children()))

    @cached_property
    def data_tool(self):
        return data_tool.get(self.__class__)(self)

    def get_children_for_user(self, user, select_related=None):
        if select_related:
            return self.children.select_related(*select_related)
        return self.children


class ProjectSet(VirtualResource, ProjectURLMixin):

    def __eq__(self, other):
        return (
            self.pootle_path == other.pootle_path
            and list(self.get_children()) == list(other.get_children()))

    def __init__(self, resources, *args, **kwargs):
        self.directory = Directory.objects.projects
        super(ProjectSet, self).__init__(resources, self.directory.pootle_path)

    @cached_property
    def data_tool(self):
        return data_tool.get(self.__class__)(self)


@receiver([post_delete, post_save])
def invalidate_accessible_projects_cache(**kwargs):
    instance = kwargs["instance"]
    # XXX: maybe use custom signals or simple function calls?
    if (instance.__class__.__name__ not in
        ['Project', 'TranslationProject', 'PermissionSet']):
        return

    cache.delete_pattern(make_method_key('Project', 'cached_dict', '*'))
    cache.delete('projects:all')
    cache.delete_pattern('projects:accessible:*')
