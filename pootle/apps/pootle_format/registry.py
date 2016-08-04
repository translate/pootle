# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

from django.utils.functional import cached_property

from pootle.core.delegate import format_registration
from pootle_format.models import FileExtension, Format


class FormatRegistry(object):

    def initialize(self):
        for filetype, info in format_registration.gather().items():
            self.register(filetype, **info)

    def register(self, name, extension, title=None, template_extension=None):
        update = False
        template_extension = template_extension or extension
        ext, created = FileExtension.objects.get_or_create(
            name=extension)
        if template_extension != extension:
            template_ext, created = FileExtension.objects.get_or_create(
                name=template_extension)
        else:
            template_ext = ext
        try:
            filetype = Format.objects.get(name=name)
        except:
            filetype = None
        if not filetype:
            filetype = Format.objects.create(
                name=name, extension=ext, template_extension=template_ext)
        if filetype.extension != ext:
            filetype.extension = ext
            update = True
        if not filetype.title:
            filetype.title = title or name.capitalize()
            update = True
        elif title and filetype.title != title:
            filetype.title = title
            update = True
        extension = filetype.template_extension.name
        if template_extension and extension != template_extension:
            template_ext, created = FileExtension.objects.get_or_create(
                name=template_extension)
            filetype.extension = template_ext
            update = True
        if update:
            filetype.save()
        if update or created:
            self.clear()
        return filetype

    def clear(self):
        if "formats" in self.__dict__:
            del self.__dict__["formats"]

    @cached_property
    def formats(self):
        formats = OrderedDict()
        for filetype in Format.objects.filter(enabled=True):
            formats[filetype.name] = dict(
                pk=filetype.pk,
                name=filetype.name,
                title=filetype.title,
                display_title=str(filetype),
                extension=str(filetype.extension),
                template_extension=str(filetype.template_extension))
        return formats

    def __iter__(self):
        return self.formats.__iter__()

    def __getitem__(self, k):
        return self.formats.__getitem__(k)

    def keys(self):
        return self.formats.keys()

    def values(self):
        return self.formats.values()

    def items(self):
        return self.formats.items()


format_registry = FormatRegistry()
