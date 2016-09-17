# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pytest_pootle.factories import (
    LanguageDBFactory, ProjectDBFactory,
    StoreDBFactory, TranslationProjectFactory)

from django.db import IntegrityError

from pootle_data.models import StoreChecksData, StoreData, TPChecksData, TPData


@pytest.mark.django_db
def test_data_store_bad(store0):
    """Test that you cant add a duplicate file extension
    """
    # needs a store
    with pytest.raises(IntegrityError):
        StoreData.objects.create()


@pytest.mark.django_db
def test_data_store(tp0):
    """Test that you cant add a duplicate file extension
    """
    store = StoreDBFactory(
        name="foo.po",
        parent=tp0.directory,
        translation_project=tp0)
    assert (
        repr(store.data)
        == '<StoreData: %s>' % store.pootle_path)


@pytest.mark.django_db
def test_data_store_checks(tp0):
    """Test that you cant add a duplicate file extension
    """
    store = StoreDBFactory(
        name="foo.po",
        parent=tp0.directory,
        translation_project=tp0)
    check_data = StoreChecksData.objects.create(store=store)
    assert (
        repr(check_data)
        == '<StoreChecksData: %s>' % store.pootle_path)


@pytest.mark.django_db
def test_data_tp_bad():
    """Test that you cant add a duplicate file extension
    """
    # needs a TP
    with pytest.raises(IntegrityError):
        TPData.objects.create()


@pytest.mark.django_db
def test_data_tp(english):
    """Test that you cant add a duplicate file extension
    """
    tp = TranslationProjectFactory(
        project=ProjectDBFactory(source_language=english),
        language=LanguageDBFactory())
    assert (
        repr(tp.data)
        == '<TPData: %s>' % tp.pootle_path)


@pytest.mark.django_db
def test_data_tp_checks(english):
    """Test that you cant add a duplicate file extension
    """
    tp = TranslationProjectFactory(
        project=ProjectDBFactory(source_language=english),
        language=LanguageDBFactory())
    check_data = TPChecksData.objects.create(tp=tp)
    assert (
        repr(check_data)
        == '<TPChecksData: %s>' % tp.pootle_path)
