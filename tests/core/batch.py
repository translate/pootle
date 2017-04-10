# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.batch import Batch
from pootle_store.models import Suggestion


@pytest.mark.django_db
def test_batch_create_reduce(store0, member):
    """The source queryset reduces as batches are created"""
    Suggestion.objects.filter(unit__store=store0).delete()
    store0.units.first().delete()
    suggestionless = store0.units.filter(suggestion__isnull=True)
    batch = Batch(Suggestion.objects, batch_size=2)
    assert batch.target == Suggestion.objects
    assert batch.batch_size == 2
    last_sugg_pk = Suggestion.objects.order_by(
        "-pk").values_list("pk", flat=True).first()

    def _create_method(unit, source, mtime):
        return dict(
            unit_id=unit,
            creation_time=mtime,
            target_f=source,
            user_id=member.id)
    batches = batch.batched_create(
        suggestionless.values_list("id", "source_f", "mtime"),
        _create_method)
    new_suggs = Suggestion.objects.filter(pk__gt=last_sugg_pk)
    assert new_suggs.count() == 0
    for batched in batches:
        assert len(batched)
        assert len(batched) <= 2
        assert all(isinstance(b, Suggestion) for b in batched)
        assert all(b.target_f == b.unit.source_f for b in batched)
    assert new_suggs.count() == store0.units.count()
    new_suggs.delete()
    created = batch.create(
        suggestionless.values_list("id", "source_f", "mtime"),
        _create_method)
    new_suggs = Suggestion.objects.filter(pk__gt=last_sugg_pk)
    assert created == new_suggs.count() == store0.units.count()
    assert (
        list(new_suggs.values_list("unit"))
        == list(store0.units.values_list("id")))


@pytest.mark.django_db
def test_batch_create_no_reduce(store0, member):
    batch = Batch(Suggestion.objects, batch_size=2)
    assert batch.target == Suggestion.objects
    assert batch.batch_size == 2
    last_sugg_pk = Suggestion.objects.order_by(
        "-pk").values_list("pk", flat=True).first()

    def _create_method(unit, source, mtime):
        return dict(
            unit_id=unit,
            creation_time=mtime,
            target_f=source,
            user_id=member.id)
    batches = batch.batched_create(
        store0.units.values_list("id", "source_f", "mtime"),
        _create_method,
        reduces=False)
    new_suggs = Suggestion.objects.filter(pk__gt=last_sugg_pk)
    assert new_suggs.count() == 0
    for batched in batches:
        assert len(batched)
        assert len(batched) <= 2
        assert all(isinstance(b, Suggestion) for b in batched)
        assert all(b.target_f == b.unit.source_f for b in batched)
    assert new_suggs.count() == store0.units.count()
    new_suggs.delete()
    created = batch.create(
        store0.units.values_list("id", "source_f", "mtime"),
        _create_method,
        reduces=False)
    new_suggs = Suggestion.objects.filter(pk__gt=last_sugg_pk)
    assert created == new_suggs.count() == store0.units.count()
    assert (
        list(new_suggs.values_list("unit"))
        == list(store0.units.values_list("id")))
