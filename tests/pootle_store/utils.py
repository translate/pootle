# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

import pytest

from translate.filters.decorators import Category
from translate.misc.multistring import multistring

from pytest_pootle.utils import create_store

from pootle.core.delegate import frozen, lifecycle
from pootle.core.user import get_system_user
from pootle_statistics.models import (
    MUTED, UNMUTED, Submission, SubmissionFields, SubmissionTypes)
from pootle_store.constants import FUZZY, TRANSLATED
from pootle_store.models import QualityCheck, Unit, UnitChange
from pootle_store.utils import UnitLifecycle


@pytest.mark.django_db
def test_frozen_unit(store0):
    unit = store0.units.first()
    frozen_unit = frozen.get(Unit)(unit)
    assert frozen_unit.source == unit.source_f
    assert frozen_unit.target == unit.target_f
    assert frozen_unit.state == unit.state
    assert frozen_unit.translator_comment == unit.translator_comment
    assert frozen_unit.revision == unit.revision


@pytest.mark.django_db
def test_unit_create(store0, member):
    unit = store0.UnitClass()
    unit.store = store0
    unit.source = multistring("Foo")
    unit.index = store0.max_index() + 1
    unit.save()
    assert unit.submission_set.count() == 0
    source = unit.unit_source
    assert source.created_by == get_system_user()
    assert source.created_with == SubmissionTypes.SYSTEM
    with pytest.raises(UnitChange.DoesNotExist):
        unit.change

    unit = store0.UnitClass()
    unit.store = store0
    unit.source = multistring("Foo2")
    unit.index = store0.max_index() + 1
    unit.save(user=member)
    assert unit.submission_set.count() == 0
    source = unit.unit_source
    assert source.created_by == member
    assert source.created_with == SubmissionTypes.SYSTEM
    with pytest.raises(UnitChange.DoesNotExist):
        unit.change

    unit = store0.UnitClass()
    unit.store = store0
    unit.source = multistring("Foo3")
    unit.index = store0.max_index() + 1
    unit.save(changed_with=SubmissionTypes.UPLOAD)
    assert unit.submission_set.count() == 0
    source = unit.unit_source
    assert source.created_by == get_system_user()
    assert source.created_with == SubmissionTypes.UPLOAD
    with pytest.raises(UnitChange.DoesNotExist):
        unit.change


@pytest.mark.django_db
def test_unit_lifecycle_instance(store0):
    unit = store0.UnitClass()
    unit.store = store0
    unit.source_f = multistring("Foo")
    unit.save()
    unit_lifecycle = lifecycle.get(Unit)(unit)
    assert isinstance(unit_lifecycle, UnitLifecycle)
    assert unit_lifecycle.original == unit._frozen
    assert unit_lifecycle.unit == unit
    assert unit_lifecycle.submission_model == unit.submission_set.model


@pytest.mark.django_db
def test_unit_lifecycle_create(store0):
    unit = store0.UnitClass()
    unit.store = store0
    unit.source_f = multistring("Foo")
    unit.save()
    source = unit.unit_source
    assert source.created_by == get_system_user()
    assert source.created_with == SubmissionTypes.SYSTEM
    with pytest.raises(UnitChange.DoesNotExist):
        unit.change


@pytest.mark.django_db
def test_unit_lifecycle_update_state(store0, member):
    unit = store0.UnitClass()
    unit.store = store0
    unit.source_f = multistring("Foo")
    unit.target_f = multistring("Bar")
    unit.state = TRANSLATED
    unit.reviewed_by = member
    unit.save(user=member)
    sub_state_update = lifecycle.get(Unit)(unit).sub_state_update()
    assert isinstance(sub_state_update, Submission)
    assert sub_state_update.unit == unit
    assert sub_state_update.translation_project == store0.translation_project
    assert sub_state_update.revision == unit.revision
    assert (
        sub_state_update.submitter
        == unit.change.submitted_by
        == member)
    assert sub_state_update.type == SubmissionTypes.SYSTEM
    assert sub_state_update.field == SubmissionFields.STATE
    assert sub_state_update.new_value == unit.state
    assert sub_state_update.old_value == unit._frozen.state
    assert not sub_state_update.pk


@pytest.mark.django_db
def test_unit_lifecycle_update_state_reviewed_by(store0, system, member2):
    unit = store0.UnitClass()
    unit.store = store0
    unit.source_f = multistring("Foo")
    unit.target_f = multistring("Bar")
    unit.state = FUZZY
    unit.save(user=system)
    # force the unit to be refrozen
    unit = unit.__class__.objects.get(id=unit.id)
    unit.state = TRANSLATED
    unit.save(reviewed_by=member2)
    sub_state_update = lifecycle.get(Unit)(unit).sub_state_update()
    assert isinstance(sub_state_update, Submission)
    assert sub_state_update.unit == unit
    assert sub_state_update.translation_project == store0.translation_project
    assert sub_state_update.revision == unit.revision
    assert (
        sub_state_update.submitter
        == unit.change.reviewed_by
        == member2)
    assert sub_state_update.type == SubmissionTypes.SYSTEM
    assert sub_state_update.field == SubmissionFields.STATE
    assert sub_state_update.new_value == unit.state
    assert sub_state_update.old_value == unit._frozen.state
    assert not sub_state_update.pk


@pytest.mark.django_db
def test_unit_lifecycle_update_comment(store0, member):
    unit = store0.UnitClass()
    unit.store = store0
    unit.source_f = multistring("Foo")
    unit.target_f = multistring("Bar")
    unit.translator_comment = "SOME COMMENT"
    unit.save(user=member)
    sub_comment_update = lifecycle.get(Unit)(unit).sub_comment_update()
    assert isinstance(sub_comment_update, Submission)
    assert sub_comment_update.unit == unit
    assert sub_comment_update.translation_project == store0.translation_project
    assert sub_comment_update.revision == unit.revision
    assert sub_comment_update.submitter == member
    assert sub_comment_update.type == SubmissionTypes.SYSTEM
    assert sub_comment_update.field == SubmissionFields.COMMENT
    assert sub_comment_update.new_value == unit.translator_comment
    assert sub_comment_update.old_value == (
        unit._frozen.translator_comment or "")
    assert not sub_comment_update.pk


@pytest.mark.django_db
def test_unit_lifecycle_update_source(store0, member):
    unit = store0.UnitClass()
    unit.store = store0
    unit.source_f = multistring("Foo")
    unit.source_f = multistring("Bar")
    unit.state = TRANSLATED
    unit.save(user=member)
    unit = Unit.objects.get(pk=unit.id)
    unit.source = multistring("Foo23")
    unit.save(user=member)
    sub_source_update = lifecycle.get(Unit)(unit).sub_source_update()
    assert isinstance(sub_source_update, Submission)
    assert sub_source_update.unit == unit
    assert sub_source_update.translation_project == store0.translation_project
    assert sub_source_update.revision == unit.revision
    assert sub_source_update.submitter == unit.change.submitted_by
    assert sub_source_update.type == SubmissionTypes.SYSTEM
    assert sub_source_update.field == SubmissionFields.SOURCE
    assert sub_source_update.new_value == unit.source_f
    assert sub_source_update.old_value == unit._frozen.source
    assert not sub_source_update.pk


@pytest.mark.django_db
def test_unit_lifecycle_update_target(store0, member):
    unit = store0.UnitClass()
    unit.store = store0
    unit.source_f = multistring("Foo")
    unit.target_f = multistring("Bar")
    unit.state = TRANSLATED
    unit.save(user=member)
    sub_target_update = lifecycle.get(Unit)(unit).sub_target_update()
    assert isinstance(sub_target_update, Submission)
    assert sub_target_update.unit == unit
    assert sub_target_update.translation_project == store0.translation_project
    assert sub_target_update.revision == unit.revision
    assert (
        sub_target_update.submitter
        == unit.change.submitted_by
        == member)
    assert sub_target_update.type == SubmissionTypes.SYSTEM
    assert sub_target_update.field == SubmissionFields.TARGET
    assert sub_target_update.new_value == unit.target_f
    assert sub_target_update.old_value == unit._frozen.target
    assert not sub_target_update.pk


@pytest.mark.django_db
def test_unit_lifecycle_mute_qc(store0, member):
    unit = store0.UnitClass()
    unit.store = store0
    unit.source_f = multistring("Foo")
    unit.save()
    unit_lifecycle = lifecycle.get(Unit)(unit)

    qc = QualityCheck(
        unit=unit,
        name="foo-check",
        message="Check foo!",
        category="Footile")

    with pytest.raises(KeyError):
        unit_lifecycle.sub_mute_qc()

    with pytest.raises(KeyError):
        unit_lifecycle.sub_mute_qc(submitter=member)

    with pytest.raises(KeyError):
        unit_lifecycle.sub_mute_qc(quality_check=qc)

    sub_mute_qc = unit_lifecycle.sub_mute_qc(
        quality_check=qc, submitter=member)

    assert sub_mute_qc.unit == unit
    assert sub_mute_qc.translation_project == store0.translation_project
    assert sub_mute_qc.revision == unit.revision
    assert sub_mute_qc.type == SubmissionTypes.WEB
    assert sub_mute_qc.field == SubmissionFields.CHECK
    assert sub_mute_qc.new_value == MUTED
    assert sub_mute_qc.old_value == UNMUTED
    assert not sub_mute_qc.pk


@pytest.mark.django_db
def test_unit_lifecycle_unmute_qc(store0, member):
    unit = store0.UnitClass()
    unit.store = store0
    unit.source_f = multistring("Foo")
    unit.save()
    unit_lifecycle = lifecycle.get(Unit)(unit)

    qc = QualityCheck(
        unit=unit,
        name="foo-check",
        message="Check foo!",
        category="Footile")

    with pytest.raises(KeyError):
        unit_lifecycle.sub_unmute_qc()

    with pytest.raises(KeyError):
        unit_lifecycle.sub_unmute_qc(submitter=member)

    with pytest.raises(KeyError):
        unit_lifecycle.sub_unmute_qc(quality_check=qc)

    sub_unmute_qc = unit_lifecycle.sub_unmute_qc(
        quality_check=qc, submitter=member)

    assert sub_unmute_qc.unit == unit
    assert sub_unmute_qc.translation_project == store0.translation_project
    assert sub_unmute_qc.revision == unit.revision
    assert sub_unmute_qc.type == SubmissionTypes.WEB
    assert sub_unmute_qc.field == SubmissionFields.CHECK
    assert sub_unmute_qc.new_value == UNMUTED
    assert sub_unmute_qc.old_value == MUTED
    assert not sub_unmute_qc.pk


@pytest.mark.django_db
def test_unit_lifecycle_create_subs(store0, member):
    unit = store0.UnitClass()
    unit.store = store0
    unit.source_f = multistring("Foo")
    unit.save()

    class DummyUnitLifecycle(UnitLifecycle):

        def sub_foo(self, **kwargs):
            self._called_foo = kwargs

        def sub_bar(self, **kwargs):
            self._called_bar = kwargs

    lc = DummyUnitLifecycle(unit)
    kwargs = dict(x=1, y=2)
    list(lc.create_subs(dict(foo=kwargs)))
    assert lc._called_foo == kwargs
    list(lc.create_subs(dict(bar=kwargs)))
    assert lc._called_bar == kwargs

    with pytest.raises(AttributeError):
        lc.update(dict(baz=kwargs))


@pytest.mark.django_db
def test_unit_lifecycle_update(store0, member):
    unit = store0.UnitClass()
    unit.store = store0
    unit.source_f = multistring("Foo")
    unit.save()

    class DummyUnitLifecycle(UnitLifecycle):

        def save_subs(self, subs):
            self._called_save = subs

        def create_subs(self, kwargs):
            self._called_create = kwargs
            return [kwargs]

    lc = DummyUnitLifecycle(unit)
    kwargs = OrderedDict((("x", 1), ("y", 2)))
    lc.update(kwargs)
    assert lc._called_create == kwargs
    assert lc._called_save == [kwargs]


@pytest.mark.django_db
def test_unit_lifecycle_calc_change(store0, member):
    unit = store0.units.first()
    unit_lifecycle = lifecycle.get(Unit)(unit)
    assert (
        unit_lifecycle.calculate_change()
        == OrderedDict())
    original_target = unit.target
    unit.state = 200
    assert (
        unit_lifecycle.calculate_change()
        == OrderedDict((("state_update", {}),)))
    unit.target = "changed target"
    assert (
        unit_lifecycle.calculate_change()
        == OrderedDict(
            (("target_update", {}),
             ("state_update", {}))))
    unit.translator_comment = "changed comment"
    assert (
        unit_lifecycle.calculate_change()
        == OrderedDict(
            (("comment_update", {}),
             ("target_update", {}),
             ("state_update", {}))))
    unit.source = "changed source"
    assert (
        unit_lifecycle.calculate_change()
        == OrderedDict(
            (("comment_update", {}),
             ("source_update", {}),
             ("target_update", {}),
             ("state_update", {}))))
    assert (
        unit_lifecycle.calculate_change(foo="bar")
        == OrderedDict(
            (("comment_update", dict(foo="bar")),
             ("source_update", dict(foo="bar")),
             ("target_update", dict(foo="bar")),
             ("state_update", dict(foo="bar")))))
    unit.target = original_target
    assert (
        unit_lifecycle.calculate_change()
        == OrderedDict(
            (("comment_update", {}),
             ("source_update", {}),
             ("state_update", {}))))


@pytest.mark.django_db
def test_unit_lifecycle_change(store0, member):
    unit = store0.UnitClass()
    unit.store = store0
    unit.source_f = multistring("Foo")
    unit.save()

    class DummyUnitLifecycle(UnitLifecycle):

        def update(self, updates):
            self._called_update = updates

        def calculate_change(self, **kwargs):
            return kwargs

    lc = DummyUnitLifecycle(unit)
    lc.change()
    assert lc._called_update == {}
    lc.change(foo="bar")
    assert lc._called_update == dict(foo="bar")


@pytest.mark.django_db
def test_mute_qualitycheck(store_po, member):
    store = create_store(pootle_path=store_po.pootle_path, units=[
        ("Hello", "", False)
    ])
    store.units[1].target = "Hello\n\nHello"
    store_po.update(store)
    unit = store_po.units.first()
    unit.save()
    check_qs = unit.qualitycheck_set.filter(
        category=Category.CRITICAL,
        false_positive=False)
    assert check_qs.count() == 1
    assert store_po.data.critical_checks == 1
    check_id = check_qs[0].id
    unit.toggle_qualitycheck(check_id=check_id, false_positive=True,
                             user=member)
    assert unit.qualitycheck_set.get(id=check_id).false_positive
    assert store_po.data.critical_checks == 0

    sub = unit.submission_set.get(quality_check__id=check_id)
    assert sub.submitter == member
