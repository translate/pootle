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

import pytest

from django.utils.encoding import force_bytes

from pootle.core.paths import Paths
from pootle_store.models import Store


@pytest.mark.django_db
def test_paths_util(project0):

    with pytest.raises(NotImplementedError):
        Paths("", "").store_qs

    class DummyPathsUtil(Paths):

        @property
        def store_qs(self):
            return Store.objects.all()

    paths_util = DummyPathsUtil(project0, "1")
    assert paths_util.context == project0
    assert paths_util.show_all is False
    assert paths_util.q == "1"
    assert (
        paths_util.rev_cache_key
        == project0.directory.revisions.get(key="stats").value)
    assert (
        paths_util.cache_key
        == ("%s.%s.%s"
            % (md5(force_bytes(paths_util.q)).hexdigest(),
               paths_util.rev_cache_key,
               paths_util.show_all)))
    assert (
        Store.objects.filter(
            translation_project__project__disabled=False).exclude(
                obsolete=True).exclude(is_template=True).filter(
                    tp_path__contains="1").count()
        == paths_util.stores.count())
    stores = set(
        st[1:] for st in paths_util.stores.values_list("tp_path", flat=True))
    dirs = set(
        ("%s/" % posixpath.dirname(path))
        for path
        in stores
        if (path.count("/") > 1))
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
    assert (
        paths_util.paths
        == sorted(
            stores | dirs,
            key=lambda path: (posixpath.dirname(path), posixpath.basename(path))))
    paths_util = DummyPathsUtil(project0, "1", show_all=True)
    assert (
        Store.objects.exclude(is_template=True).filter(
            tp_path__contains="1").count()
        == paths_util.stores.count())
    stores = set(
        st[1:] for st in paths_util.stores.values_list("tp_path", flat=True))
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
    assert (
        paths_util.paths
        == sorted(
            stores | dirs,
            key=lambda path: (posixpath.dirname(path), posixpath.basename(path))))
    assert (
        paths_util.paths
        == sorted(
            stores | dirs,
            key=lambda path: (posixpath.dirname(path), posixpath.basename(path))))
