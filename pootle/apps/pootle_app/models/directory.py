#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2012 Zuza Software Foundation
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

from django.db import models

from pootle_misc.aggregate import max_column
from pootle_misc.baseurl import l
from pootle_misc.util import cached_property, dictsum, getfromcache
from pootle_store.models import Suggestion, Unit
from pootle_store.util import (empty_quickstats, empty_completestats,
                               statssum, completestatssum, suggestions_sum)


class DirectoryManager(models.Manager):

    def get_query_set(self):
        # ForeignKey fields with null=True are not selected by
        # select_related unless explicitly specified
        return super(DirectoryManager, self).get_query_set() \
                                            .select_related('parent')

    def _get_root(self):
        return self.get(pootle_path='/')
    root = property(_get_root)

    def _get_projects(self):
        return self.get(pootle_path='/projects/')
    projects = property(_get_projects)


class Directory(models.Model):

    class Meta:
        ordering = ['name']
        app_label = "pootle_app"

    is_dir = True

    name = models.CharField(max_length=255, null=False)
    parent = models.ForeignKey('Directory', related_name='child_dirs',
            null=True, db_index=True)
    pootle_path = models.CharField(max_length=255, null=False, db_index=True)

    objects = DirectoryManager()

    def save(self, *args, **kwargs):
        if self.parent is not None:
            self.pootle_path = self.parent.pootle_path + self.name + '/'
        else:
            self.pootle_path = '/'

        super(Directory, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        for store in self.stores.iterator():
            store.delete()

        super(Directory, self).delete(*args, **kwargs)

    def get_relative(self, path):
        """Given a path of the form a/b/c, where the path is relative
        to this directory, recurse the path and return the object
        (either a Directory or a Store) named 'c'.

        This does not currently deal with .. path components."""

        from pootle_store.models import Store

        if path not in (None, ''):
            pootle_path = '%s%s' % (self.pootle_path, path)
            try:
                return Directory.objects.get(pootle_path=pootle_path)
            except Directory.DoesNotExist, e:
                try:
                    return Store.objects.get(pootle_path=pootle_path)
                except Store.DoesNotExist:
                    raise e
        else:
            return self

    @getfromcache
    def get_mtime(self):
        return max_column(Unit.objects.filter(
            store__pootle_path__startswith=self.pootle_path
        ), 'mtime', None)

    def _get_stores(self):
        """Queryset with all descending stores."""
        from pootle_store.models import Store
        return Store.objects.filter(pootle_path__startswith=self.pootle_path)
    stores = property(_get_stores)

    @cached_property
    def path(self):
        """Returns just the path part omitting language and project codes.

        If the `pootle_path` of a :cls:`Directory` object `dir` is
        `/af/project/dir1/dir2/file.po`, `dir.path` will return
        `dir1/dir2/file.po`.
        """
        return u'/'.join(self.pootle_path.split(u'/')[3:])

    def get_or_make_subdir(self, child_name):
        child_dir, created = Directory.objects.get_or_create(name=child_name,
                                                             parent=self)
        return child_dir

    def __unicode__(self):
        return self.pootle_path

    def get_absolute_url(self):
        return l(self.pootle_path)

    @getfromcache
    def getquickstats(self):
        """Calculate aggregate stats for all directory based on stats
        of all descending stores and dirs."""
        if self.is_template_project:
            #FIXME: Hackish return empty_stats to avoid messing up
            # with project and language stats
            return empty_quickstats

        #FIXME: can we replace this with a quicker path query?
        file_result = statssum(self.child_stores.iterator())
        dir_result = statssum(self.child_dirs.iterator())
        stats = dictsum(file_result, dir_result)
        return stats


    @getfromcache
    def getcompletestats(self):
        if self.is_template_project:
            return empty_completestats

        file_result = completestatssum(self.child_stores.iterator())
        dir_result = completestatssum(self.child_dirs.iterator())

        stats = {}
        for cat in set(file_result) | set(dir_result):
            stats[cat] = dictsum(file_result.get(cat, {}),
                                 dir_result.get(cat, {}))

        return stats


    @getfromcache
    def get_suggestion_stats(self):
        file_result = suggestions_sum(self.child_stores.iterator())
        dir_result = suggestions_sum(self.child_dirs.iterator())
        return file_result + dir_result


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
            return Directory.objects.filter(pootle_path__in=parents) \
                                    .order_by('pootle_path')

        return Directory.objects.none()

    def get_suggestion_count(self):
        """check if any child store has suggestions"""
        return Suggestion.objects.filter(
            unit__store__pootle_path__startswith=self.pootle_path).count()

    def is_language(self):
        """does this directory point at a language"""
        return self.pootle_path.count('/') == 2

    def is_project(self):
        return (self.pootle_path.startswith('/projects/') and
                self.pootle_path.count('/') == 3)

    def is_translationproject(self):
        """does this directory point at a translation project"""
        return (self.pootle_path.count('/') == 3 and not
                self.pootle_path.startswith('/projects/'))

    is_template_project = property(lambda self: self.pootle_path
                                                    .startswith('/templates/'))

    @cached_property
    def translation_project(self):
        """Returns the translation project belonging to this directory."""
        if self.is_language() or self.is_project():
            return None
        else:
            if self.is_translationproject():
                return self.translationproject
            else:
                aux_dir = self
                while (not aux_dir.is_translationproject() and
                       aux_dir.parent is not None):
                    aux_dir = aux_dir.parent

                return aux_dir.translationproject

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
