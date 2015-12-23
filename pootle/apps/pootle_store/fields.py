#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""Fields required for handling translation files"""

import logging
import os

from translate.misc.multistring import multistring

from django.db import models
from django.db.models.fields.files import FieldFile, FileField


# # # # # # # # # String # # # # # # # # # # # # # # #

SEPARATOR = "__%$%__%$%__%$%__"
PLURAL_PLACEHOLDER = "__%POOTLE%_$NUMEROUS$__"


def list_empty(strings):
    """check if list is exclusively made of empty strings.

    useful for detecting empty multistrings and storing them as a
    simple empty string in db.
    """
    for string in strings:
        if len(string) > 0:
            return False
    return True


def to_db(value):
    """Flatten the given value (string, list of plurals or multistring) into
    the database string representation.
    """
    if value is None:
        return None
    elif isinstance(value, multistring):
        if list_empty(value.strings):
            return ''
        else:
            return SEPARATOR.join(value.strings)
    elif isinstance(value, list):
        if list_empty(value):
            return ''
        else:
            return SEPARATOR.join(value)
    else:
        return value


def to_python(value):
    """Reconstruct a multistring from the database string representation."""
    if not value:
        return multistring("", encoding="UTF-8")
    elif isinstance(value, multistring):
        return value
    elif isinstance(value, basestring):
        strings = value.split(SEPARATOR)
        if strings[-1] == PLURAL_PLACEHOLDER:
            strings = strings[:-1]
            plural = True
        else:
            plural = len(strings) > 1
        ms = multistring(strings, encoding="UTF-8")
        ms.plural = plural
        return ms
    elif isinstance(value, dict):
        return multistring([val for key, val in sorted(value.items())],
                           encoding="UTF-8")
    else:
        return multistring(value, encoding="UTF-8")


class MultiStringField(models.Field):
    description = \
        "a field imitating translate.misc.multistring used for plurals"
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        super(MultiStringField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return "TextField"

    def to_python(self, value):
        return to_python(value)

    def get_prep_value(self, value):
        return to_db(value)

    def get_prep_lookup(self, lookup_type, value):
        if (lookup_type in ('exact', 'iexact') or
            not isinstance(value, basestring)):
            value = self.get_prep_value(value)
        return super(MultiStringField, self).get_prep_lookup(lookup_type,
                                                             value)


# # # # # # # # # File # # # # # # # # # # # # # # # #


class StoreTuple(object):
    """Encapsulates toolkit stores in the in memory cache, needed
    since LRUCachingDict is based on a weakref.WeakValueDictionary
    which cannot reference normal tuples
    """

    def __init__(self, store, mod_info, realpath):
        self.store = store
        self.mod_info = mod_info
        self.realpath = realpath


class TranslationStoreFieldFile(FieldFile):
    """FieldFile is the file-like object of a FileField, that is found in a
    TranslationStoreField.
    """

    from translate.misc.lru import LRUCachingDict
    from django.conf import settings

    _store_cache = LRUCachingDict(settings.PARSE_POOL_SIZE,
                                  settings.PARSE_POOL_CULL_FREQUENCY)

    def getpomtime(self):
        file_stat = os.stat(self.realpath)
        return file_stat.st_mtime, file_stat.st_size

    @property
    def filename(self):
        return os.path.basename(self.name)

    def _get_realpath(self):
        """Return realpath resolving symlinks if necessary."""
        if not hasattr(self, "_realpath"):
            # Django's db.models.fields.files.FieldFile raises ValueError if
            # if the file field has no name - and tests "if self" to check
            if self:
                self._realpath = os.path.realpath(self.path)
            else:
                self._realpath = ''
        return self._realpath

    @property
    def realpath(self):
        """Get real path from cache before attempting to check for symlinks."""
        if not hasattr(self, "_store_tuple"):
            return self._get_realpath()
        else:
            return self._store_tuple.realpath

    @property
    def store(self):
        """Get translation store from dictionary cache, populate if store not
        already cached.
        """
        self._update_store_cache()
        return self._store_tuple.store

    def _update_store_cache(self):
        """Add translation store to dictionary cache, replace old cached
        version if needed.
        """
        if self.exists():
            mod_info = self.getpomtime()
        else:
            mod_info = 0
        if (not hasattr(self, "_store_tuple") or
            self._store_tuple.mod_info != mod_info):
            try:
                self._store_tuple = self._store_cache[self.path]
                if self._store_tuple.mod_info != mod_info:
                    # if file is modified act as if it doesn't exist in cache
                    raise KeyError
            except KeyError:
                logging.debug(u"Cache miss for %s", self.path)
                from translate.storage import factory
                from pootle_store.filetypes import factory_classes

                store_obj = factory.getobject(self.path,
                                              ignore=self.field.ignore,
                                              classes=factory_classes)
                self._store_tuple = StoreTuple(store_obj, mod_info,
                                               self.realpath)
                self._store_cache[self.path] = self._store_tuple

    def _touch_store_cache(self):
        """Update stored mod_info without reparsing file."""
        if hasattr(self, "_store_tuple"):
            mod_info = self.getpomtime()
            if self._store_tuple.mod_info != mod_info:
                self._store_tuple.mod_info = mod_info
        else:
            # FIXME: do we really need that?
            self._update_store_cache()

    def _delete_store_cache(self):
        """Remove translation store from cache."""
        try:
            del self._store_cache[self.path]
        except KeyError:
            pass

        try:
            del self._store_tuple
        except AttributeError:
            pass

    def exists(self):
        return os.path.exists(self.realpath)

    def savestore(self):
        """Saves to temporary file then moves over original file. This way we
        avoid the need for locking.
        """
        import shutil
        from pootle_misc import ptempfile as tempfile
        tmpfile, tmpfilename = tempfile.mkstemp(suffix=self.filename)
        os.close(tmpfile)
        self.store.savefile(tmpfilename)
        shutil.move(tmpfilename, self.realpath)
        self._touch_store_cache()

    def save(self, name, content, save=True):
        # FIXME: implement save to tmp file then move instead of directly
        # saving
        super(TranslationStoreFieldFile, self).save(name, content, save)
        self._delete_store_cache()

    def delete(self, save=True):
        self._delete_store_cache()
        if save:
            super(TranslationStoreFieldFile, self).delete(save)


class TranslationStoreField(FileField):
    """This is the field class to represent a FileField in a model that
    represents a translation store.
    """

    attr_class = TranslationStoreFieldFile

    def __init__(self, ignore=None, **kwargs):
        """ignore: postfix to be stripped from filename when trying to
        determine file format for parsing, useful for .pending files
        """
        self.ignore = ignore
        super(TranslationStoreField, self).__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(TranslationStoreField,
                                         self).deconstruct()
        if self.ignore is not None:
            kwargs['ignore'] = self.ignore
        return name, path, args, kwargs
