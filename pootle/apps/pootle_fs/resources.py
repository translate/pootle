# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


from pootle_fs.models import StoreFS
from pootle_store.models import Store


class FSProjectResources(object):

    def __init__(self, project):
        self.project = project

    def __str__(self):
        return (
            "<%s(%s)>"
            % (self.__class__.__name__,
               self.project))

    @property
    def stores(self):
        return Store.objects.filter(
            translation_project__project=self.project)

    @property
    def tracked(self):
        return StoreFS.objects.filter(
            project=self.project).select_related("store")

    @property
    def synced(self):
        return (
            self.tracked.exclude(last_sync_revision__isnull=True)
                        .exclude(last_sync_hash__isnull=True))

    @property
    def unsynced(self):
        return (
            self.tracked.filter(last_sync_revision__isnull=True)
                        .filter(last_sync_hash__isnull=True))

    @property
    def trackable_stores(self):
        return self.stores.exclude(obsolete=True).filter(fs__isnull=True)
