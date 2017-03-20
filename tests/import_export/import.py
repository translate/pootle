# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

import pytest

from django.core.files.uploadedfile import SimpleUploadedFile

import pytest_pootle
from pytest_pootle.utils import create_store

from import_export.exceptions import UnsupportedFiletypeError
from import_export.utils import import_file
from pootle_app.models.permissions import check_user_permission
from pootle_statistics.models import SubmissionTypes
from pootle_store.constants import NEW, OBSOLETE, PARSED, TRANSLATED
from pootle_store.models import Store, Unit


IMPORT_SUCCESS = "headers_correct.po"
IMPORT_UNSUPP_FILE = "tutorial.ts"


def _import_file(file_name, file_dir=None,
                 content_type="text/x-gettext-translation",
                 user=None):
    if not file_dir:
        file_dir = os.path.join(
            os.path.dirname(pytest_pootle.__file__),
            "data/po/tutorial/en")

    with open(os.path.join(file_dir, file_name), "r") as f:
        import_file(
            SimpleUploadedFile(file_name, f.read(), content_type),
            user=user)


@pytest.mark.django_db
def test_import_success(project0_nongnu, store0, admin):
    store0.sync()
    assert store0.state == NEW
    _import_file(IMPORT_SUCCESS, user=admin)
    store = Store.objects.get(pk=store0.pk)
    assert store.state == PARSED


@pytest.mark.django_db
def test_import_failure(po_directory, en_tutorial_po,
                        file_import_failure, member):
    filename, exception = file_import_failure
    with pytest.raises(exception):
        _import_file(filename, user=member)


@pytest.mark.django_db
def test_import_unsupported(po_directory, en_tutorial_ts,
                            ts_directory, member):
    with pytest.raises(UnsupportedFiletypeError):
        _import_file(IMPORT_UNSUPP_FILE,
                     file_dir=os.path.join(ts_directory, "tutorial/en"),
                     content_type="text/vnd.trolltech.linguist",
                     user=member)


@pytest.mark.django_db
def test_import_new_file(project0_nongnu, import_tps, site_users):
    tp = import_tps
    user = site_users["user"]
    store_pootle_path = tp.pootle_path + "import_new_file.po"
    filestore = create_store(store_pootle_path, "0",
                             [("Unit Source", "Unit Target", False)])

    # New store can't be created via current import command. This test will
    # need to be adjusted if we allow to create new stores via import command.
    from import_export.exceptions import FileImportError
    with pytest.raises(FileImportError):
        import_file(SimpleUploadedFile("import_new_file.po",
                                       str(filestore),
                                       "text/x-gettext-translation"), user)


@pytest.mark.django_db
def test_import_to_empty(project0_nongnu, import_tps, site_users):
    from pytest_pootle.factories import StoreDBFactory

    tp = import_tps
    user = site_users["user"]
    store = StoreDBFactory(translation_project=tp, name="import_to_empty.po")
    filestore = create_store(store.pootle_path, "0",
                             [("Unit Source", "Unit Target", False)])
    import_file(SimpleUploadedFile(store.name,
                                   str(filestore),
                                   "text/x-gettext-translation"), user)

    allow_add_and_obsolete = ((tp.project.checkstyle == 'terminology'
                               or tp.is_template_project)
                              and check_user_permission(user,
                                                        'administrate',
                                                        tp.directory))
    if allow_add_and_obsolete:
        assert tp.stores.get(pootle_path=store.pootle_path).units.count() == 1
        unit_source = store.units[0].unit_source
        assert unit_source.created_with == SubmissionTypes.UPLOAD
        assert unit_source.created_by == user
        assert store.units[0].change.changed_with == SubmissionTypes.UPLOAD
        assert store.units[0].change.submitted_by == user
    else:
        assert tp.stores.get(pootle_path=store.pootle_path).units.count() == 0


@pytest.mark.django_db
def test_import_add_and_obsolete_units(project0_nongnu, import_tps,
                                       site_users):
    from pytest_pootle.factories import StoreDBFactory, UnitDBFactory

    tp = import_tps
    user = site_users["user"]
    store = StoreDBFactory(translation_project=tp)
    unit = UnitDBFactory(store=store, state=TRANSLATED)
    filestore = create_store(
        store.pootle_path,
        "0",
        [(unit.source_f + " REPLACED", unit.target_f + " REPLACED", False)])
    import_file(SimpleUploadedFile("import_add_and_obsolete.po",
                                   str(filestore),
                                   "text/x-gettext-translation"), user)

    allow_add_and_obsolete = ((tp.project.checkstyle == 'terminology'
                               or tp.is_template_project)
                              and check_user_permission(user,
                                                        'administrate',
                                                        tp.directory))
    if allow_add_and_obsolete:
        assert Unit.objects.filter(store=store, state=OBSOLETE).count() == 1
        assert store.units.filter(state=TRANSLATED).count() == 1
        unit_source = store.units[0].unit_source
        assert unit_source.created_with == SubmissionTypes.UPLOAD
        assert unit_source.created_by == user
        assert store.units[0].change.changed_with == SubmissionTypes.UPLOAD
        assert store.units[0].change.submitted_by == user
        assert Unit.objects.filter(store=store).count() == 2
    else:
        assert store.units.all().count() == 1
