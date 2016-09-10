# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


from pootle_store.unit.search import DBSearchBackend


class VFolderDBSearchBackend(DBSearchBackend):

    def __init__(self, request_user, **kwargs):
        self.vfolder = kwargs.pop("vfolder")
        super(VFolderDBSearchBackend, self).__init__(request_user, **kwargs)

    def filter_qs(self, qs):
        filtered = super(VFolderDBSearchBackend, self).filter_qs(qs)
        return filtered.filter(store__vfolders=self.vfolder)
