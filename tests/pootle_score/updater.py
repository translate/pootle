# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.delegate import score_data_updater
from pootle_store.models import Store
from pootle_score.updater import StoreScoreUpdater


@pytest.mark.django_db
def test_score_store_updater(store0, admin):
    updater = score_data_updater.get(Store)(store=store0, user=admin)
    assert updater.store == store0
    assert updater.user == admin
    assert isinstance(updater, StoreScoreUpdater)
