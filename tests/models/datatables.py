# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.db import IntegrityError

from pootle_data.models import StoreData, TPData


@pytest.mark.django_db
def test_data_store_bad(store0):
    """Test that you cant add a duplicate file extension
    """
    # needs a store
    with pytest.raises(IntegrityError):
        StoreData.objects.create()


@pytest.mark.django_db
def test_data_store(store0):
    """Test that you cant add a duplicate file extension
    """
    data = StoreData.objects.create(store=store0)
    assert (
        repr(data)
        == '<StoreData: %s>' % store0.pootle_path)


@pytest.mark.django_db
def test_data_tp_bad():
    """Test that you cant add a duplicate file extension
    """
    # needs a TP
    with pytest.raises(IntegrityError):
        TPData.objects.create()


@pytest.mark.django_db
def test_data_tp(tp0):
    """Test that you cant add a duplicate file extension
    """
    data = TPData.objects.create(tp=tp0)
    assert (
        repr(data)
        == '<TPData: %s>' % tp0.pootle_path)
