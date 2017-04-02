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
        template_extension = template_extension or extension
        exts = {}
        for ext in set([extension, template_extension]):
            exts[ext], __ = FileExtension.objects.get_or_create(name=ext)
        kwargs = dict(
            name=name,
            defaults=dict(
                extension=exts[extension],
                template_extension=exts[template_extension]))
        if title:
            kwargs["defaults"]["title"] = title
        filetype, created = self.format_qs.update_or_create(**kwargs)
        self.clear()
        return filetype

    def clear(self):
        if "formats" in self.__dict__:
            del self.__dict__["formats"]

    @property
    def format_qs(self):
        return Format.objects.select_related(
            "extension", "template_extension")

    @cached_property
    def formats(self):
        formats = OrderedDict()
        for filetype in self.format_qs.filter(enabled=True):
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
