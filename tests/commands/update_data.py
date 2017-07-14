# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.management import call_command


@pytest.mark.cmd
@pytest.mark.django_db
def test_update_data_noargs(store0):
    """Site wide update_data"""
    total_words = store0.data.total_words
    critical_checks = store0.data.critical_checks
    store0.data.total_words = 0
    store0.data.critical_checks = 0
    store0.data.save()
    call_command("update_data")
    store0.data.refresh_from_db()
    assert store0.data.total_words == total_words
    assert store0.data.critical_checks == critical_checks


@pytest.mark.cmd
@pytest.mark.django_db
def test_update_data_project(store0):
    """Site wide update_data"""
    total_words = store0.data.total_words
    critical_checks = store0.data.critical_checks
    store0.data.total_words = 0
    store0.data.critical_checks = 0
    store0.data.save()
    call_command(
        "update_data",
        "--project",
        store0.translation_project.project.code)
    store0.data.refresh_from_db()
    assert store0.data.total_words == total_words
    assert store0.data.critical_checks == critical_checks


@pytest.mark.cmd
@pytest.mark.django_db
def test_update_data_language(store0):
    """Site wide update_data"""
    total_words = store0.data.total_words
    critical_checks = store0.data.critical_checks
    store0.data.total_words = 0
    store0.data.critical_checks = 0
    store0.data.save()
    call_command(
        "update_data",
        "--language",
        store0.translation_project.language.code)
    store0.data.refresh_from_db()
    assert store0.data.total_words == total_words
    assert store0.data.critical_checks == critical_checks


@pytest.mark.cmd
@pytest.mark.django_db
def test_update_data_store(store0):
    """Site wide update_data"""
    total_words = store0.data.total_words
    critical_checks = store0.data.critical_checks
    store0.data.total_words = 0
    store0.data.critical_checks = 0
    store0.data.save()
    call_command(
        "update_data",
        "--store",
        store0.pootle_path)
    store0.data.refresh_from_db()
    assert store0.data.total_words == total_words
    assert store0.data.critical_checks == critical_checks
