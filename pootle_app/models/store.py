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

from django.db import models
from django.db.models.signals import pre_save
from django.utils.translation import ugettext_lazy as _

from Pootle.pootlefile import relative_real_path, absolute_real_path

from directory import Directory

class StoreManager(models.Manager):
    def get_query_set(self, *args, **kwargs):
        return super(StoreManager, self).get_query_set(*args, **kwargs).select_related(depth=1)

class Store(models.Model):
    """A model representing a translation store (i.e. a PO or XLIFF file)."""

    objects = StoreManager()
    
    is_dir = False

    class Meta:
        app_label = "pootle_app"
        ordering = ['name']
        unique_together = ('parent', 'name')

    real_path   = models.FilePathField()
    # Uncomment the line below when the Directory model comes into use
    parent      = models.ForeignKey(Directory, related_name='child_stores')
    # The filesystem path of the store.
    name        = models.CharField(max_length=255, null=False)
    pootle_path = models.CharField(max_length=1024, null=False)

    def _get_abs_real_path(self):
        return absolute_real_path(self.real_path)

    def _set_abs_real_path(self, value):
        self.real_path = relative_real_path(value)

    abs_real_path = property(_get_abs_real_path, _set_abs_real_path)

    def __str__(self):
        return self.name

def set_store_pootle_path(sender, instance, **kwargs):
    instance.pootle_path = '%s%s' % (instance.parent.pootle_path, instance.name)

pre_save.connect(set_store_pootle_path, sender=Store)

class UnitManager(models.Manager):
    def get_or_make(self, store, index, source, target):
        try:
            return self.get(store=store, index=index, source=source, target=target)
        except self.model.DoesNotExist:
            unit = Unit(store=store, index=index, source=source, target=target)
            unit.save()
            return unit

class Unit(models.Model):
    class Meta:
        app_label = "pootle_app"

    objects = UnitManager()

    store   = models.ForeignKey(Store, related_name='units', db_index=True)
    index   = models.IntegerField(db_index=True)
    source  = models.TextField()
    target  = models.TextField()
    state   = models.CharField(max_length=255, db_index=True)
