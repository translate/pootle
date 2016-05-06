# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging

import dirsync

from .plugin import Plugin


class LocalFSPlugin(Plugin):

    fs_type = "localfs"
    _pulled = False

    def push(self, response):
        dirsync.sync(
            self.project.local_fs_path,
            self.fs_url,
            "sync",
            purge=True,
            logger=logging.getLogger(dirsync.__name__))
        return response

    def pull(self):
        dirsync.sync(
            self.fs_url,
            self.project.local_fs_path,
            "sync",
            create=True,
            purge=True,
            logger=logging.getLogger(dirsync.__name__))
