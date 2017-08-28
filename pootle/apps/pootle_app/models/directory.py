# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property

from pootle.core.delegate import data_tool
from pootle.core.mixins import CachedTreeItem
from pootle.core.url_helpers import get_editor_filter, split_pootle_path
from pootle_misc.baseurl import l
from pootle_revision.models import Revision


class DirectoryManager(models.Manager):

    def live(self):
        """Filters non-obsolete directories."""
        return self.filter(obsolete=False)

    @cached_property
    def root(self):
        return self.get(pootle_path='/')

    @cached_property
    def projects(self):
        return self.get(pootle_path='/projects/')


def validate_no_slashes(value):
    if '/' in value:
        raise ValidationError('Directory name cannot contain "/" characters')

    if '\\' in value:
        raise ValidationError('Directory name cannot contain "\\" characters')


class Directory(models.Model, CachedTreeItem):

    # any changes to the `name` field may require updating the schema
    # see migration 0005_case_sensitive_schema.py
    name = models.CharField(max_length=255, null=False, blank=True,
                            validators=[validate_no_slashes])
    parent = models.ForeignKey('Directory', related_name='child_dirs',
                               null=True, blank=True, db_index=True,
                               on_delete=models.CASCADE)
    # any changes to the `pootle_path` field may require updating the schema
    # see migration 0005_case_sensitive_schema.py
    pootle_path = models.CharField(max_length=255, null=False, db_index=True,
                                   unique=True, default='/')
    tp = models.ForeignKey(
        'pootle_translationproject.TranslationProject',
        related_name='dirs',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True)
    tp_path = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True)
    obsolete = models.BooleanField(default=False)
    revisions = GenericRelation(Revision)

    is_dir = True

    objects = DirectoryManager()

    class Meta(object):
        ordering = ['name']
        default_permissions = ()
        app_label = "pootle_app"
        index_together = [
            ["obsolete", "pootle_path"],
            ["obsolete", "tp", "tp_path"]]
        base_manager_name = "objects"

    @cached_property
    def data_tool(self):
        return data_tool.get(self.__class__)(self)

    # # # # # # # # # # # # # #  Properties # # # # # # # # # # # # # # # # # #

    @property
    def code(self):
        return self.name.replace('.', '-')

    # # # # # # # # # # # # # #  Cached properties # # # # # # # # # # # # # #

    @cached_property
    def path(self):
        """Returns just the path part omitting language and project codes."""
        return self.tp_path

    @cached_property
    def translation_project(self):
        """Returns the translation project belonging to this directory."""
        if self.tp_id is not None:
            return self.tp
        return self.translationproject

    # # # # # # # # # # # # # #  Methods # # # # # # # # # # # # # # # # # # #

    def __unicode__(self):
        return self.pootle_path

    def __init__(self, *args, **kwargs):
        super(Directory, self).__init__(*args, **kwargs)

    def clean(self):
        if self.parent is not None:
            self.pootle_path = self.parent.pootle_path + self.name + '/'
        set_tp_path = (
            self.parent is not None
            and self.parent.parent is not None
            and self.parent.name != "projects")
        if set_tp_path:
            self.tp_path = (
                "/"
                if self.parent.tp_path is None
                else "/".join([self.parent.tp_path.rstrip("/"),
                               self.name, ""]))

        if self.name == '' and self.parent is not None:
            raise ValidationError('Name can be empty only for root directory.')

        if self.parent is None and self.name != '':
            raise ValidationError('Parent can be unset only for root '
                                  'directory.')

    def save(self, *args, **kwargs):
        # Force validation of fields.
        self.full_clean(validate_unique=False)
        super(Directory, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return l(self.pootle_path)

    def get_translate_url(self, **kwargs):
        lang_code, proj_code, dir_path = split_pootle_path(self.pootle_path)[:3]

        if lang_code and proj_code:
            pattern_name = 'pootle-tp-translate'
            pattern_args = [lang_code, proj_code, dir_path]
        elif lang_code:
            pattern_name = 'pootle-language-translate'
            pattern_args = [lang_code]
        elif proj_code:
            pattern_name = 'pootle-project-translate'
            pattern_args = [proj_code]
        else:
            pattern_name = 'pootle-projects-translate'
            pattern_args = []

        return u''.join([
            reverse(pattern_name, args=pattern_args),
            get_editor_filter(**kwargs),
        ])

    # # # TreeItem
    def get_children(self):
        result = []
        if not self.is_projects_root():
            # FIXME: can we replace this with a quicker path query?
            result.extend([item for item in
                           self.child_stores.live().iterator()])
            result.extend([item for item in self.child_dirs.live().iterator()])
        else:
            project_list = [item.project for item in self.child_dirs.iterator()
                            if not item.project.disabled]
            result.extend(project_list)

        return result

    def get_parents(self):
        if self.parent:
            if self.is_translationproject():
                return self.translationproject.get_parents()
            elif self.is_project():
                return self.project.get_parents()
            elif self.is_language():
                return self.language.get_parents()
            elif self.parent.is_translationproject():
                return [self.parent.translationproject]
            else:
                return [self.parent]
        else:
            return []

    # # # /TreeItem

    def get_or_make_subdir(self, child_name):
        child_dir, created = Directory.objects.get_or_create(
            name=child_name,
            parent=self)
        if created and self.tp:
            child_dir.tp = self.tp
            child_dir.save()
        return child_dir

    def trail(self, only_dirs=True):
        """Returns a list of ancestor directories excluding
        :cls:`~pootle_translationproject.models.TranslationProject` and above.
        """
        path_parts = self.pootle_path.split('/')
        parents = []
        if only_dirs:
            # skip language, and translation_project directories
            start = 4
        else:
            start = 1

        for i in xrange(start, len(path_parts)):
            path = '/'.join(path_parts[:i]) + '/'
            parents.append(path)

        if parents:
            return Directory.objects.live().filter(pootle_path__in=parents) \
                                           .order_by('pootle_path')

        return Directory.objects.none()

    def is_language(self):
        """does this directory point at a language"""
        return (self.pootle_path.count('/') == 2 and
                not self.pootle_path.startswith('/projects/'))

    def is_project(self):
        return (self.pootle_path.startswith('/projects/') and
                self.pootle_path.count('/') == 3)

    def is_translationproject(self):
        """does this directory point at a translation project"""
        return (self.pootle_path.count('/') == 3 and not
                self.pootle_path.startswith('/projects/'))

    def is_projects_root(self):
        """is this directory a projects root directory"""
        return self.pootle_path == '/projects/'

    def delete(self, *args, **kwargs):

        self.initialize_children()
        for item in self.children:
            item.delete()

        super(Directory, self).delete(*args, **kwargs)

    def makeobsolete(self, *args, **kwargs):
        """Make this directory and all its children obsolete"""

        self.initialize_children()
        for item in self.children:
            item.makeobsolete()

        self.obsolete = True
        self.save()
