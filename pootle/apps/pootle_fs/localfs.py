# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os
import uuid

import dirsync

from django import forms

from pootle.core.delegate import revision
from pootle_project.models import Project

from .exceptions import FSFetchError
from .plugin import Plugin


class LocalFSPlugin(Plugin):

    fs_type = "localfs"
    _pulled = False

    @property
    def latest_hash(self):
        return revision.get(Project)(
            self.project).get(key="pootle.fs.fs_hash")

    def push(self, response):
        dirsync.sync(
            self.project.local_fs_path,
            self.fs_url,
            "sync",
            purge=True,
            logger=logging.getLogger(dirsync.__name__))
        return response

    def fetch(self):
        try:
            synced = dirsync.sync(
                self.fs_url,
                self.project.local_fs_path,
                "sync",
                create=True,
                purge=True,
                logger=logging.getLogger(dirsync.__name__))
        except ValueError as e:
            raise FSFetchError(e)
        if synced:
            revision.get(Project)(self.project).set(
                keys=["pootle.fs.fs_hash"], value=uuid.uuid4().hex)


class LocalFSUrlValidator(object):

    help_text = "Enter an absolute path to a directory on your filesystem"

    def validate(self, url):
        if not os.path.isabs(url):
            raise forms.ValidationError(self.help_text)
