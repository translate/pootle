# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""Fields required for handling translation files"""

import os

from translate.misc.multistring import multistring

from django.db import models
from django.db.models.fields.files import FieldFile, FileField
from django.utils.functional import cached_property

from pootle.core.utils.multistring import (parse_multistring,
                                           unparse_multistring)


# # # # # # # # # String # # # # # # # # # # # # # # #


def to_db(value):
    """Flatten the given value (string, list of plurals or multistring) into
    the database string representation.
    """
    if value is None:
        return None

    return unparse_multistring(value)


def to_python(value):
    """Reconstruct a multistring from the database string representation."""
    if not value:
        return multistring("", encoding="UTF-8")
    elif isinstance(value, multistring):
        return value
    elif isinstance(value, basestring):
        return parse_multistring(value)
    elif isinstance(value, dict):
        return multistring([val for __, val in sorted(value.items())],
                           encoding="UTF-8")
    else:
        return multistring(value, encoding="UTF-8")


class CastOnAssignDescriptor(object):
    """
    A property descriptor which ensures that `field.to_python()` is called on
    _every_ assignment to the field.  This used to be provided by the
    `django.db.models.subclassing.Creator` class, which in turn was used by the
    deprecated-in-Django-1.10 `SubfieldBase` class, hence the reimplementation
    here.
    """

    def __init__(self, field):
        self.field = field

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        return obj.__dict__[self.field.name]

    def __set__(self, obj, value):
        obj.__dict__[self.field.name] = self.field.to_python(value)


class MultiStringField(models.Field):
    description = \
        "a field imitating translate.misc.multistring used for plurals"

    def __init__(self, *args, **kwargs):
        super(MultiStringField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return "TextField"

    def to_python(self, value):
        return to_python(value)

    def from_db_value(self, value, expression, connection, context):
        return to_python(value)

    def get_prep_value(self, value):
        return to_db(value)

    def get_prep_lookup(self, lookup_type, value):
        if (lookup_type in ('exact', 'iexact') or
            not isinstance(value, basestring)):
            value = self.get_prep_value(value)
        return super(MultiStringField, self).get_prep_lookup(lookup_type,
                                                             value)

    def contribute_to_class(self, cls, name):
        super(MultiStringField, self).contribute_to_class(cls, name)
        setattr(cls, name, CastOnAssignDescriptor(self))


# # # # # # # # # File # # # # # # # # # # # # # # # #


class TranslationStoreFieldFile(FieldFile):
    """FieldFile is the file-like object of a FileField, that is found in a
    TranslationStoreField.
    """

    def getpomtime(self):
        file_stat = os.stat(self.realpath)
        return file_stat.st_mtime, file_stat.st_size

    @property
    def filename(self):
        return os.path.basename(self.name)

    @cached_property
    def realpath(self):
        """Get real path from cache before attempting to check for symlinks."""
        if self:
            return os.path.realpath(self.path)
        else:
            return ''

    @cached_property
    def store(self):
        """Get translation store from dictionary cache, populate if store not
        already cached.
        """
        from translate.storage import factory

        fileclass = self.instance.syncer.file_class
        classes = {
            str(self.instance.filetype.extension): fileclass,
            str(self.instance.filetype.template_extension): fileclass}
        return factory.getobject(
            self.path,
            ignore=self.field.ignore,
            classes=classes)

    def exists(self):
        return os.path.exists(self.realpath)

    def savestore(self):
        """Saves to temporary file then moves over original file. This way we
        avoid the need for locking.
        """
        import shutil
        from pootle.core.utils import ptempfile as tempfile
        tmpfile, tmpfilename = tempfile.mkstemp(suffix=self.filename)
        os.close(tmpfile)
        self.store.savefile(tmpfilename)
        shutil.move(tmpfilename, self.realpath)
        if "store" in self.__dict__:
            del self.__dict__["store"]

    def save(self, name, content, save=True):
        # FIXME: implement save to tmp file then move instead of directly
        # saving
        super(TranslationStoreFieldFile, self).save(name, content, save)
        if "store" in self.__dict__:
            del self.__dict__["store"]

    def delete(self, save=True):
        if "store" in self.__dict__:
            del self.__dict__["store"]
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
