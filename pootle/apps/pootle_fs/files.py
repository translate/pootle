
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import io
import logging
import os

from translate.storage.factory import getclass

from django.contrib.auth import get_user_model
from django.utils.functional import cached_property

from pootle.core.models import Revision
from pootle_statistics.models import SubmissionTypes
from pootle_store.constants import POOTLE_WINS, SOURCE_WINS
from pootle_store.models import Store


logger = logging.getLogger(__name__)


class FSFile(object):

    def __init__(self, store_fs):
        """
        :param store_fs: ``StoreFS`` object
        """
        from .models import StoreFS

        if not isinstance(store_fs, StoreFS):
            raise TypeError(
                "pootle_fs.FSFile expects a StoreFS")
        self.store_fs = store_fs
        self.pootle_path = store_fs.pootle_path
        self.path = store_fs.path

    def __str__(self):
        return "<%s: %s::%s>" % (
            self.__class__.__name__, self.pootle_path, self.path)

    def __hash__(self):
        return hash(
            "%s::%s::%s::%s"
            % (self.path,
               self.pootle_path,
               self.store_fs.last_sync_hash,
               self.store_fs.last_sync_revision))

    def __eq__(self, other):
        return hash(other) == hash(self)

    @property
    def file_exists(self):
        return os.path.exists(self.file_path)

    @property
    def store_exists(self):
        return self.store is not None

    @property
    def file_path(self):
        return os.path.join(
            self.store_fs.project.local_fs_path,
            self.path.strip("/"))

    @property
    def fs_changed(self):
        latest_hash = self.latest_hash
        return (
            latest_hash is not None
            and (
                latest_hash
                != self.store_fs.last_sync_hash))

    @property
    def latest_hash(self):
        if self.file_exists:
            return str(os.stat(self.file_path).st_mtime)

    @property
    def pootle_changed(self):
        return bool(
            self.store_exists
            and (
                (self.store.data.max_unit_revision or 0)
                != self.store_fs.last_sync_revision))

    @cached_property
    def store(self):
        return self.store_fs.store

    def create_store(self):
        """
        Creates a ```Store``` and if necessary the ```TranslationProject```
        parent ```Directories```
        """
        store = Store.objects.create_by_path(
            self.pootle_path,
            project=self.store_fs.project)
        self.store_fs.store = store
        self.store_fs.save()
        self.__dict__["store"] = self.store_fs.store

    def delete(self):
        """
        Delete the file from FS and Pootle

        This does not commit/push
        """
        store = self.store
        if store and store.pk:
            store.makeobsolete()
            del self.__dict__["store"]
        if self.store_fs.pk:
            self.store_fs.delete()
        self.remove_file()

    def on_sync(self):
        """
        Called after FS and Pootle have been synced
        """
        self.store_fs.resolve_conflict = None
        self.store_fs.staged_for_merge = False
        self.store_fs.last_sync_hash = self.latest_hash
        self.store_fs.last_sync_revision = self.store.data.max_unit_revision
        self.store_fs.save()
        logger.debug("File synced: %s", self.path)

    def pull(self, user=None, merge=False, pootle_wins=None):
        """
        Pull FS file into Pootle
        """
        if self.store_exists and not self.fs_changed:
            return
        logger.debug("Pulling file: %s", self.path)
        if not self.store_exists:
            self.create_store()
        self._sync_to_pootle(user=user, merge=merge, pootle_wins=pootle_wins)

    def push(self, user=None):
        """
        Push Pootle ``Store`` into FS
        """
        dont_push = (
            not self.store_exists
            or (self.file_exists and not self.pootle_changed))
        if dont_push:
            return
        logger.debug("Pushing file: %s", self.path)
        directory = os.path.dirname(self.file_path)
        if not os.path.exists(directory):
            logger.debug("Creating directory: %s", directory)
            os.makedirs(directory)
        self._sync_from_pootle()

    def read(self):
        if not self.file_exists:
            return
        with open(self.file_path) as f:
            return f.read()

    def remove_file(self):
        if self.file_exists:
            os.unlink(self.file_path)

    def deserialize(self):
        if not self.file_exists:
            return
        deserialized = ""
        with open(self.file_path) as f:
            deserialized = f.read()
        if self.store_exists:
            return self.store.deserialize(deserialized)
        serial_io = io.BytesIO(deserialized)
        return getclass(serial_io)(serial_io.read())

    def serialize(self):
        if not self.store_exists:
            return
        return self.store.serialize()

    def _sync_from_pootle(self):
        """
        Update FS file with the serialized content from Pootle ```Store```
        """
        with open(self.file_path, "w") as f:
            f.write(self.serialize())
        logger.debug("Pushed file: %s", self.path)

    def _sync_to_pootle(self, merge=False, user=None, pootle_wins=None):
        """
        Update Pootle ``Store`` with the parsed FS file.
        """
        User = get_user_model()
        if pootle_wins is None:
            resolve_conflict = (
                self.store_fs.resolve_conflict or SOURCE_WINS)
        elif pootle_wins:
            resolve_conflict = POOTLE_WINS
        else:
            resolve_conflict = SOURCE_WINS
        if merge:
            revision = self.store_fs.last_sync_revision or 0
        else:
            # We set the revision to *anything* higher than the Store's
            # This is analogous to the `overwrite` option in
            # Store.update_from_disk
            revision = Revision.get() + 1
        tmp_store = self.deserialize()
        self.store.update(
            tmp_store,
            submission_type=SubmissionTypes.SYSTEM,
            user=user or User.objects.get_system_user(),
            store_revision=revision,
            resolve_conflict=resolve_conflict)
        logger.debug("Pulled file: %s", self.path)
