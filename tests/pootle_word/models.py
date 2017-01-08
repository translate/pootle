# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from pootle_word.models import Stem


@pytest.mark.django_db
def test_word_stem_repr(store0):
    stem = Stem.objects.create(root="foo")
    assert repr(stem) == "<Stem: \"foo\", units: []>"
    unit_stem = stem.units.through
    unit_stem.objects.bulk_create(
        unit_stem(stem=stem, unit_id=unit)
        for unit
        in store0.units[:5].values_list("id", flat=True))
    assert (
        repr(stem)
        == ("<Stem: \"foo\", units: %s>"
            % list(stem.units.values_list("id", flat=True))))


@pytest.mark.django_db
def test_word_stem_instance(store0):
    stem1 = Stem.objects.create(root="foo")
    unit_stem = stem1.units.through
    unit_stem.objects.bulk_create(
        unit_stem(stem=stem1, unit_id=unit)
        for unit
        in store0.units[:5].values_list("id", flat=True))
    stem2 = Stem.objects.create(root="brows")
    unit_stem = stem2.units.through
    unit_stem.objects.bulk_create(
        unit_stem(stem=stem2, unit_id=unit)
        for unit
        in store0.units[:5].values_list("id", flat=True))
    for unit in store0.units[:5]:
        stems = unit.stems.all()
        assert stem1 in stems
        assert stem2 in stems


@pytest.mark.django_db
def test_word_stem_bad_no_root(store0):
    with pytest.raises(ValidationError):
        Stem.objects.create()


@pytest.mark.django_db
def test_word_stem_bad_dupe(store0):
    Stem.objects.create(root="foo")
    with pytest.raises(ValidationError):
        Stem.objects.create(root="foo")


@pytest.mark.django_db
def test_word_stem_bad_dupe_unit(store0):
    stem = Stem.objects.create(root="foo")
    stem.units.through.objects.create(
        stem=stem, unit=store0.units[0])
    with pytest.raises(IntegrityError):
        stem.units.through.objects.create(
            stem=stem, unit=store0.units[0])
