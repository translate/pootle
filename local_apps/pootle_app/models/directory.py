#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2009 Zuza Software Foundation
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

from django.db                import models
from django.db.models.signals import pre_delete, pre_save
from django.utils.translation import ugettext_lazy as _
from pootle_store.util import dictsum, statssum, completestatssum
from pootle_misc.util import getfromcache

class DirectoryManager(models.Manager):
    def get_query_set(self, *args, **kwargs):
        return super(DirectoryManager, self).get_query_set(*args, **kwargs).select_related(depth=1)

    def _get_root(self):
        return self.get(parent=None)

    root = property(_get_root)

def filter_goals(query, goal):
    if goal is None:
        return query
    else:
        return query.filter(goals=goal)

def filter_next_store(query, store_name):
    if store_name is None:
        return query
    else:
        return query.filter(name__gte=store_name)

class Directory(models.Model):
    class Meta:
        ordering = ['name']
        app_label = "pootle_app"


    is_dir = True

    name        = models.CharField(max_length=255, null=False, db_index=True)
    parent      = models.ForeignKey('Directory', related_name='child_dirs', null=True)
    pootle_path = models.CharField(max_length=1024, null=False)

    objects = DirectoryManager()
        
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

    def filter_stores(self, search=None, starting_store=None):
        if search is None:
            return filter_next_store(filter_goals(self.child_stores, None), starting_store)
        elif search.contains_only_file_specific_criteria():
            return filter_next_store(filter_goals(self.child_stores, search.goal), starting_store)
        else:
            raise Exception("Can't filter on unit-specific information")

    def get_or_make_subdir(self, child_name):
        try:
            return self.child_dirs.get(name=child_name)
        except Directory.DoesNotExist:
            child_dir = Directory(name=child_name, parent=self)
            child_dir.save()
            return child_dir

    def __unicode__(self):
        return self.pootle_path

    @getfromcache
    def getquickstats(self):
        """calculate aggregate stats for all directory based on stats
        of all descenging stores and dirs"""

        #FIXME: can we replace this with a quicker path query? 
        file_result = statssum(self.child_stores.all())
        dir_result  = statssum(self.child_dirs.all())
        stats = dictsum(file_result, dir_result)
        return stats

    @getfromcache
    def getcompletestats(self, checker):
        file_result = completestatssum(self.child_stores.all(), checker)
        dir_result  = completestatssum(self.child_dirs.all(), checker)
        stats = dictsum(file_result, dir_result)
        return stats
    
def delete_children(sender, instance, **kwargs):
    """Before deleting a directory, delete all its children."""
    for child_store in instance.child_stores.all():
        child_store.delete()

    for child_dir in instance.child_dirs.all():
        child_dir.delete()

pre_delete.connect(delete_children, sender=Directory)

def set_directory_pootle_path(sender, instance, **kwargs):
    if instance.parent is not None:
        instance.pootle_path = '%s%s/' % (instance.parent.pootle_path, instance.name)
    else:
        instance.pootle_path = '/'

pre_save.connect(set_directory_pootle_path, sender=Directory)


