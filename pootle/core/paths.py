# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pathlib
import posixpath
from hashlib import md5

from django.utils.encoding import force_bytes

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
            % (md5(force_bytes(self.q)).hexdigest(),
               self.rev_cache_key,
               self.show_all))

    @property
    def store_qs(self):
        raise NotImplementedError

    @property
    def stores(self):
        stores = self.store_qs.exclude(obsolete=True)
        if not self.show_all:
            stores = stores.exclude(
                translation_project__project__disabled=True)
        return stores.exclude(is_template=True).filter(
            tp_path__contains=self.q).order_by()

    @persistent_property
    def paths(self):
        stores = set(
            st[1:]
            for st
            in self.stores.values_list("tp_path", flat=True))
        dirs = set()
        for store in stores:
            if posixpath.dirname(store) in dirs:
                continue
            dirs = (
                dirs
                | (set(
                    "%s/" % str(p)
                    for p
                    in pathlib.PosixPath(store).parents
                    if str(p) != ".")))
        return sorted(
            dirs | stores,
            key=lambda path: (posixpath.dirname(path), posixpath.basename(path)))
