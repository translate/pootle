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


"""
Utility functions for handling translation files.
"""
import logging

from django.core.files import File
from django.db.models.fields.files import FieldFile, FileField

from translate.storage import factory

class TranslationStoreFile(File):
    """
    A mixin for use alongside django.core.files.base.File, which provides
    additional features for dealing with translation files.
    """
    def _test(self):
        print self.store
        


class TranslationStoreFieldFile(FieldFile, TranslationStoreFile):
    _store_cache = {}

    def _get_store(self):
        """ get translation store from dictionary cache, populate if
        store not already cached. """
        if self.path not in self._store_cache:
            self._update_store_cache()
        return self._store_cache[self.path][0]

    def _update_store_cache(self):
        """ add translation store to dictionary cache, replace old
        cached version if needed."""
        mod_info = statsdb.get_mod_info(self.path)

        if self.path not in self._store_cache or self._store_cache[self.path][1] != mod_info:
            logging.debug("cache miss for %s", self.path)
            self._store_cache[self.path] = (factory.getobject(self.path), mod_info)

    def _delete_store_cache(self):
        """ remove traslation store from dictionary cache."""
        if self.path in self._store_cache:
            del(self._store_cache[self.path])

    store = property(_get_store)
    
    def save(self, name, content, save=True):
        #FIXME: implement save to tmp file then move instead of directly saving
        super(TranslationStoreFieldFile, self).save(name, content, save)
        self._update_store_cache()
        
    def delete(self, save=True):
        self._delete_store_cache()
        super(TranslationStoreFieldFile, self).delete(save)

class TranslationStoreField(FileField):
    attr_class = TranslationStoreFieldFile

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.FileField}
        defaults.update(kwargs)
        return super(TranslationStoreField, self).formfield(**defaults)

