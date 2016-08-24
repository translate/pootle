# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.utils.aggregate import max_column


class StoreRevision(object):

    def __init__(self, store):
        self.store = store

    def get_max_unit_revision(self):
        return max_column(
            self.store.unit_set.all(), 'revision', 0)

    def update(self):
        current_revision = self.get_max_unit_revision()
        if current_revision != self.store.revision:
            self.store.revision = current_revision
            self.store.save()
