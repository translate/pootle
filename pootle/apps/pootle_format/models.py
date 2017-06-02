# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db import models

from .abstracts import AbstractFileExtension, AbstractFormat


class FileExtension(AbstractFileExtension):

    class Meta(AbstractFileExtension.Meta):
        db_table = "pootle_fileextension"


class Format(AbstractFormat):

    class Meta(AbstractFormat.Meta):
        db_table = "pootle_format"

    extension = models.ForeignKey(
        FileExtension, related_name="formats", on_delete=models.CASCADE)
    template_extension = models.ForeignKey(
        FileExtension, related_name="template_formats",
        on_delete=models.CASCADE)

    def __str__(self):
        return (
            "%s (%s/%s)"
            % (self.title,
               self.extension,
               self.template_extension))
