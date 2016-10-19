# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.functional import cached_property

from pootle.core.delegate import data_tool
from pootle.core.mixins import CachedTreeItem
from pootle.core.url_helpers import (get_editor_filter, split_pootle_path,
                                     to_tp_relative_path)
from pootle_misc.baseurl import l


class DirectoryManager(models.Manager):
    use_for_related_fields = True

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
                               null=True, blank=True, db_index=True)
    # any changes to the `pootle_path` field may require updating the schema
    # see migration 0005_case_sensitive_schema.py
    pootle_path = models.CharField(max_length=255, null=False, db_index=True,
                                   unique=True, default='/')
    obsolete = models.BooleanField(default=False)

    is_dir = True

    objects = DirectoryManager()

    class Meta(object):
        ordering = ['name']
        default_permissions = ()
        app_label = "pootle_app"

    @cached_property
    def data_tool(self):
        return data_tool.get(self.__class__)(self)

    # # # # # # # # # # # # # #  Properties # # # # # # # # # # # # # # # # # #

    @property
    def stores(self):
        """Queryset with all descending stores."""
        from pootle_store.models import Store
        return Store.objects.live() \
                            .filter(pootle_path__startswith=self.pootle_path)

    @property
    def is_template_project(self):
        return self.pootle_path.startswith('/templates/')

    @property
    def is_root(self):
        """Tell if this directory is the root directory."""
        return self.pootle_path == '/'

    @property
    def code(self):
        return self.name.replace('.', '-')

    # # # # # # # # # # # # # #  Cached properties # # # # # # # # # # # # # #

    @cached_property
    def path(self):
        """Returns just the path part omitting language and project codes."""
        return to_tp_relative_path(self.pootle_path)

    @cached_property
    def translation_project(self):
        """Returns the translation project belonging to this directory."""
        if self.is_language() or self.is_project():
            return None

        if self.is_translationproject():
            return self.translationproject

        aux_dir = self
        while not aux_dir.is_translationproject() and aux_dir.parent is not None:
            aux_dir = aux_dir.parent

        return aux_dir.translationproject

    # # # # # # # # # # # # # #  Methods # # # # # # # # # # # # # # # # # # #

    def __unicode__(self):
        return self.pootle_path

    def __init__(self, *args, **kwargs):
        super(Directory, self).__init__(*args, **kwargs)

    def clean(self):
        if self.parent is not None:
            self.pootle_path = self.parent.pootle_path + self.name + '/'

        if self.name == '' and self.parent is not None:
            raise ValidationError('Name can be empty only for root directory.')

        if self.parent is None and self.name != '':
            raise ValidationError('Parent can be unset only for root '
                                  'directory.')

    def save(self, *args, **kwargs):
        # Force validation of fields.
        self.full_clean()

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

    def get_relative(self, path):
        """Given a path of the form a/b/c, where the path is relative
        to this directory, recurse the path and return the object
        (either a Directory or a Store) named 'c'.

        This does not currently deal with .. path components.
        """

        from pootle_store.models import Store

        if path not in (None, ''):
            pootle_path = '%s%s' % (self.pootle_path, path)
            try:
                return Directory.objects.live().get(pootle_path=pootle_path)
            except Directory.DoesNotExist as e:
                try:
                    return Store.objects.live().get(pootle_path=pootle_path)
                except Store.DoesNotExist:
                    raise e
        else:
            return self

    def get_or_make_subdir(self, child_name):
        child_dir = Directory.objects.get_or_create(name=child_name,
                                                    parent=self)[0]
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

    def get_real_path(self):
        """physical filesystem path for directory"""
        if self.is_project():
            return self.project.code

        translation_project = self.translation_project
        if self.is_translationproject():
            return translation_project.real_path

        if translation_project:
            tp_path = translation_project.pootle_path
            path_prefix = self.pootle_path[len(tp_path)-1:-1]
            return translation_project.real_path + path_prefix

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
