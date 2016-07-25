# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
from collections import OrderedDict

from .exceptions import UnrecognizedFiletype


class ProjectFiletypes(object):

    def __init__(self, project):
        self.project = project

    @property
    def filetypes(self):
        return self.project.filetypes.all()

    def choose_filetype(self, filename):
        ext = os.path.splitext(filename)[1][1:]
        formats = self.project.filetypes.filter(
            extension__name=ext)
        if formats.exists():
            return formats.first()
        formats = self.project.filetypes.filter(
            template_extension__name=ext)
        if formats.count():
            return formats.first()
        filetypes = (
            ", ".join(
                self.project.filetypes.values_list(
                    "extension__name", flat=True)))

        # The filename's extension is not recognised in this Project
        raise UnrecognizedFiletype(
            "File '%s' is not recognized for Project "
            "'%s', available extensions are %s"
            % (filename,
               self.project.fullname,
               filetypes))

    @property
    def filetype_extensions(self):
        return list(
            self.filetypes.values_list(
                "extension__name", flat=True))

    @property
    def template_extensions(self):
        return list(
            self.filetypes.values_list(
                "template_extension__name", flat=True))

    @property
    def valid_extensions(self):
        """this is the equiv of combining 2 sets"""
        return list(
            OrderedDict.fromkeys(
                self.filetype_extensions
                + self.template_extensions))
