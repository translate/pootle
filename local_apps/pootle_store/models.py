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
from django.conf import settings
from django.core.files.storage import FileSystemStorage

#FIXME: move this stuff to pootle_store
from pootle_app.models.store_file import relative_real_path, absolute_real_path
from pootle_app.models.directory import Directory

from pootle_store.fields import TranslationStoreField

# custom storage otherwise djago assumes all files are uploads headed to
# media dir
fs = FileSystemStorage(location=settings.PODIRECTORY)

class Store(models.Model):
    """A model representing a translation store (i.e. a PO or XLIFF file)."""
    is_dir = False
    
    file        = TranslationStoreField(upload_to="fish", max_length=255, storage=fs, db_index=True)
    parent      = models.ForeignKey(Directory, related_name='child_stores', db_index=True)
    pootle_path = models.CharField(max_length=255, null=False, unique=True, db_index=True)
    name        = models.CharField(max_length=128, null=False)

    class Meta:
        ordering = ['pootle_path']
        unique_together = ('parent', 'name')

    def _get_abs_real_path(self):
        return self.file.path

    def _set_abs_real_path(self, value):
        self.file.path = absolute_real_path(value)

    abs_real_path = property(_get_abs_real_path, _set_abs_real_path)

    def _get_real_path(self):
        return self.file.name

    def _set_real_path(self, value):
        self.file.name = relative_real_path(value)

    real_path = property(_get_real_path, _set_real_path)

    def __unicode__(self):
        return self.name
    
def set_store_pootle_path(sender, instance, **kwargs):
    instance.pootle_path = '%s%s' % (instance.parent.pootle_path, instance.name)

models.signals.pre_save.connect(set_store_pootle_path, sender=Store)

class Unit(models.Model):
    #FIXME: why do we have this model, what is it used for
    
    store = models.ForeignKey(Store, related_name='units', db_index=True)
    index = models.IntegerField(db_index=True)
    source = models.TextField()
    #FIXME: what about plurals
    target = models.TextField()
    state = models.CharField(max_length=255, db_index=True)
