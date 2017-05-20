# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import posixpath

from pootle.core.decorators import persistent_property
from pootle.core.delegate import revision


class Paths(object):

    def __init__(self, context, q, show_all=False):
        self.context = context
        self.q = q
        self.show_all = show_all

    @property
    def rev_cache_key(self):
        return revision.get(
            self.context.directory.__class__)(
                self.context.directory).get(key="stats")

    @property
    def cache_key(self):
        return (
            "%s.%s.%s"
            % (self.q,
               self.rev_cache_key,
               self.show_all))

    @property
    def store_qs(self):
        raise NotImplementedError

    @property
    def stores(self):
        stores = self.store_qs
        if not self.show_all:
            stores = stores.exclude(
                translation_project__project__disabled=True).exclude(
                    obsolete=True)
        return stores.exclude(is_template=True).filter(
            tp_path__contains=self.q).order_by()

    @persistent_property
    def paths(self):
        stores = set(
            st[1:]
            for st
            in self.stores.values_list("tp_path", flat=True))
        dirs = set(
            ("%s/" % posixpath.dirname(path))
            for path
            in stores
            if (path.count("/") > 1
                and self.q in path))
        return sorted(dirs | stores)
