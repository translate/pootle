# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.exceptions import MissingHandlerError

from .delegate import (
    fs_post_pull_handlers, fs_post_push_handlers,
    fs_pre_pull_handlers, fs_pre_push_handlers)


class FSHandlers(object):
    """Calls handlers that are configured for a Project in order on FS
    push/pull events
    """

    plugin_config = None
    plugin_handlers = None

    def __init__(self, plugin):
        self.plugin = plugin

    @property
    def handlers(self):
        if self.plugin_handlers is None:
            raise NotImplementedError
        return self.plugin_handlers.gather(self.plugin__class__)

    @property
    def handler_config(self):
        if self.plugin_config is None:
            raise NotImplementedError
        return self.plugin.project.config.get(self.plugin_config, [])

    def send(self, **kwargs):
        for handler in self.handler_config:
            if handler not in self.handlers:
                raise MissingHandlerError(
                    "Handler '%s' not found for project '%s'"
                    % (handler, self.plugin.project))
            self.handlers[handler](**kwargs)


class FSPrePushHandlers(FSHandlers):
    plugin_config = "pootle_fs.pre_push"
    plugin_handlers = fs_pre_push_handlers


class FSPostPushHandlers(FSHandlers):
    plugin_config = "pootle_fs.post_push"
    plugin_handlers = fs_post_push_handlers


class FSPrePullHandlers(FSHandlers):
    plugin_config = "pootle_fs.pre_pull"
    plugin_handlers = fs_pre_pull_handlers


class FSPostPullHandlers(FSHandlers):
    plugin_config = "pootle_fs.post_pull"
    plugin_handlers = fs_post_pull_handlers
