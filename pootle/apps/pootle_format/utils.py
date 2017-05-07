# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os
from collections import OrderedDict

from django.utils.functional import cached_property

from pootle_fs.utils import PathFilter

from .exceptions import UnrecognizedFiletype


log = logging.getLogger(__name__)


class ProjectFiletypes(object):

    def __init__(self, project):
        self.project = project

    @property
    def filetypes(self):
        return self.project.filetypes.all()

    def choose_filetype(self, filename):
        ext = os.path.splitext(filename)[1][1:]
        filetypes = self.filetypes.select_related(
            "extension", "template_extension")
        filetypes = list(
            filetypes.filter(extension__name=ext)
            | filetypes.filter(template_extension__name=ext))
        for filetype in filetypes:
            if filetype.extension.name == ext:
                return filetype
        for filetype in filetypes:
            if filetype.template_extension.name == ext:
                return filetype
        raise self.unrecognized_file(filename)

    def unrecognized_file(self, filename):
        # The filename's extension is not recognised in this Project
        return UnrecognizedFiletype(
            "File '%s' is not recognized for Project "
            "'%s', available extensions are %s"
            % (filename,
               self.project.fullname,
               ", ".join(set(self.filetype_extensions))))

    def unrecognized_filetype(self, filename):
        # The filetype is not recognized for the project
        return UnrecognizedFiletype(
            "Filetype '%s' is not recognized for Project "
            "'%s', available filetypes are %s"
            % (filename,
               self.project.fullname,
               ", ".join(str(ft) for ft in self.filetypes)))

    @cached_property
    def filetype_extensions(self):
        return list(
            self.filetypes.values_list(
                "extension__name", flat=True))

    @cached_property
    def template_extensions(self):
        return list(
            self.filetypes.values_list(
                "template_extension__name", flat=True))

    @cached_property
    def valid_extensions(self):
        """this is the equiv of combining 2 sets"""
        exts = []
        template_exts = []
        filetypes = self.filetypes.values_list(
            "extension__name", "template_extension__name")
        for ext, template_ext in filetypes.iterator():
            exts.append(ext)
            template_exts.append(template_ext)
        return list(
            OrderedDict.fromkeys(exts + template_exts))

    def add_filetype(self, filetype):
        """Adds a filetype to a Project"""
        if filetype not in self.filetypes:
            log.info(
                "Adding filetype '%s' to project '%s'",
                filetype, self.project)
            self.project.filetypes.add(filetype)
            self.clear_cache()

    def clear_cache(self):
        cached = [
            "filetype_extensions",
            "template_extensions",
            "valid_extensions"]
        for cachetype in cached:
            if cachetype in self.__dict__:
                del self.__dict__[cachetype]

    def set_store_filetype(self, store, filetype):
        """Sets a Store to given filetype

        If `from_filetype` is given, only updates if current filetype matches
        """
        if filetype not in self.filetypes:
            raise self.unrecognized_filetype(filetype)
        log.info(
            "Setting filetype '%s' to store '%s'",
            filetype, store.pootle_path)
        store.filetype = filetype
        # update the extension if required
        extension = (
            store.is_template
            and str(filetype.template_extension)
            or str(filetype.extension))
        root_name = os.path.splitext(store.name)[0]
        new_name = (
            root_name.endswith(".%s" % extension)
            and root_name
            or ("%s.%s"
                % (root_name, extension)))
        if store.name != new_name:
            store.name = new_name
        store.save()

    def _tp_path_regex(self, tp, matching):
        """Creates a regex from

        /tp/path/$glob_converted_to_regex.($valid_extensions)$
        """
        extensions = (
            (tp == self.project.get_template_translationproject())
            and self.template_extensions
            or self.filetype_extensions)
        return (
            r"^/%s\.%s$"
            % (PathFilter().path_regex(matching).rstrip("$"),
               r"(%s)" % ("|".join(extensions))))

    def set_tp_filetype(self, tp, filetype, from_filetype=None, matching=None):
        """Set all Stores in TranslationProject to given filetype

        If `from_filetype` is given, only Stores of that type will be updated

        If `matching` is given its treated as a glob matching pattern to be
        appended to the tp part of the pootle_path - ie `/lang/proj/$glob`
        """
        stores = tp.stores.exclude(filetype=filetype)
        if matching:
            stores = stores.filter(
                tp_path__regex=self._tp_path_regex(tp, matching))
        if from_filetype:
            stores = stores.filter(filetype=from_filetype)
        for store in stores.iterator():
            self.set_store_filetype(store, filetype)

    def set_filetypes(self, filetype, from_filetype=None, matching=None):
        """Set all Stores in Project to given filetype

        If `from_filetype` is given, only Stores of that type will be updated

        If `matching` is given its treated as a glob matching pattern to be
        appended to the tp part of the pootle_path - ie `/lang/proj/$glob`
        """
        if filetype not in self.filetypes:
            raise self.unrecognized_filetype(filetype)
        templates = self.project.get_template_translationproject()
        if templates:
            # set the templates tp filetypes
            self.set_tp_filetype(
                templates,
                filetype,
                from_filetype=from_filetype,
                matching=matching)
        for tp in self.project.translationproject_set.all():
            # set the other tp filetypes
            if tp == templates:
                continue
            self.set_tp_filetype(
                tp,
                filetype,
                from_filetype=from_filetype,
                matching=matching)
