
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.exceptions import MissingPluginError, NotConfiguredError

from .delegate import fs_plugins


class FSPlugin(object):
    """Wraps a Project to access the configured FS plugin"""

    def __init__(self, project):
        self.project = project
        plugins = fs_plugins.gather(self.project.__class__)
        fs_type = project.config.get("pootle_fs.fs_type")
        fs_url = project.config.get("pootle_fs.fs_url")
        if not fs_type or not fs_url:
            raise NotConfiguredError()
        try:
            self.plugin = plugins[fs_type](self.project)
        except KeyError:
            raise MissingPluginError(
                "No such plugin: %s" % fs_type)

    def __getattr__(self, k):
        return getattr(self.plugin, k)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.project == other.project)

    def __str__(self):
        return str(self.plugin)
