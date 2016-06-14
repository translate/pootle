# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


@pytest.fixture
def project0_fs_resources():
    from pootle_fs.models import StoreFS
    from pootle_project.models import Project
    from pootle_store.models import Store

    project = Project.objects.get(code="project0")
    stores = Store.objects.filter(
        translation_project__project=project)
    batch = int(stores.count() / 4)
    StoreFS.objects.all().delete()
    for store in stores[0:batch]:
        store.makeobsolete()
    for store in stores[batch:batch * 2]:
        StoreFS.objects.create(
            store=store,
            path="/some/fs%s" % store.pootle_path)
        store.makeobsolete()
    for store in stores[batch * 2:batch * 3]:
        StoreFS.objects.create(
            store=store,
            path="/some/fs%s" % store.pootle_path)
    return project
