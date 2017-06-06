# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import check_updater, crud
from pootle.core.plugin import getter
from pootle_store.models import QualityCheck, Store
from pootle_translationproject.models import TranslationProject

from .utils import QualityCheckCRUD, StoreQCUpdater, TPQCUpdater


qc_crud = QualityCheckCRUD()


@getter(crud, sender=QualityCheck)
def data_crud_getter(**kwargs):
    return qc_crud


@getter(check_updater, sender=TranslationProject)
def get_tp_check_updater(**kwargs_):
    return TPQCUpdater


@getter(check_updater, sender=Store)
def get_store_check_updater(**kwargs_):
    return StoreQCUpdater
