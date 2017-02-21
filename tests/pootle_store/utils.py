# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from translate.misc.multistring import multistring

from pootle.core.delegate import frozen, lifecycle
from pootle.core.user import get_system_user
from pootle_statistics.models import (
    Submission, SubmissionFields, SubmissionTypes)
from pootle_store.constants import TRANSLATED
from pootle_store.models import QualityCheck, Unit, UnitChange
from pootle_store.utils import UnitLifecycle


@pytest.mark.django_db
def test_frozen_unit(store0):
    unit = store0.units.first()
    frozen_unit = frozen.get(Unit)(unit)
    assert frozen_unit.source == unit.source_f
    assert frozen_unit.target == unit.target_f
    assert frozen_unit.state == unit.state
    assert frozen_unit.translator_comment == unit.getnotes(origin="translator")


@pytest.mark.django_db
def test_unit_lifecycle_instance(store0):
    unit = store0.UnitClass()
    unit.store = store0
    unit.source_f = multistring("Foo")
    unit.index = store0.max_index() + 1
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
    unit.index = store0.max_index() + 1
    unit.save()
    source = unit.unit_source.get()
    assert source.created_by == get_system_user()
    assert source.created_with == SubmissionTypes.SYSTEM


@pytest.mark.django_db
def test_unit_lifecycle_update_state(store0, member):
    unit = store0.UnitClass()
    unit.store = store0
    unit.source_f = multistring("Foo")
    unit.target_f = multistring("Bar")
    unit.state = TRANSLATED
    unit.index = store0.max_index() + 1
    unit.change = UnitChange(
        unit=unit,
        reviewed_by=member,
        changed_with=SubmissionTypes.SYSTEM)
    unit.save()
    sub_state_update = lifecycle.get(Unit)(unit).sub_state_update()
    assert isinstance(sub_state_update, Submission)
    assert sub_state_update.unit == unit
    assert sub_state_update.store == store0
    assert sub_state_update.translation_project == store0.translation_project
    assert sub_state_update.revision == unit.revision
    assert sub_state_update.submitter == unit.change.reviewed_by
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
    unit.comment = "SOME COMMENT"
    unit.index = store0.max_index() + 1
    unit.commented_by = member
    unit.save()
    sub_comment_update = lifecycle.get(Unit)(unit).sub_comment_update()
    assert isinstance(sub_comment_update, Submission)
    assert sub_comment_update.unit == unit
    assert sub_comment_update.store == store0
    assert sub_comment_update.translation_project == store0.translation_project
    assert sub_comment_update.revision == unit.revision
    assert sub_comment_update.submitter == unit.commented_by
    assert sub_comment_update.type == SubmissionTypes.SYSTEM
    assert sub_comment_update.field == SubmissionFields.COMMENT
    assert sub_comment_update.new_value == unit.translator_comment
    assert sub_comment_update.old_value == unit._frozen.translator_comment
    assert not sub_comment_update.pk


@pytest.mark.django_db
def test_unit_lifecycle_update_source(store0, member):
    unit = store0.UnitClass()
    unit.store = store0
    unit.source_f = multistring("Foo")
    unit.source_f = multistring("Bar")
    unit.state = TRANSLATED
    unit.index = store0.max_index() + 1
    unit.change = UnitChange(
        unit=unit,
        submitted_by=member,
        changed_with=SubmissionTypes.SYSTEM)
    unit.save()
    sub_source_update = lifecycle.get(Unit)(unit).sub_source_update()
    assert isinstance(sub_source_update, Submission)
    assert sub_source_update.unit == unit
    assert sub_source_update.store == store0
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
    unit.index = store0.max_index() + 1
    unit.change = UnitChange(
        unit=unit,
        submitted_by=member,
        changed_with=SubmissionTypes.SYSTEM)
    unit.save()
    sub_target_update = lifecycle.get(Unit)(unit).sub_target_update()
    assert isinstance(sub_target_update, Submission)
    assert sub_target_update.unit == unit
    assert sub_target_update.store == store0
    assert sub_target_update.translation_project == store0.translation_project
    assert sub_target_update.revision == unit.revision
    assert sub_target_update.submitter == unit.change.submitted_by
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
    unit.index = store0.max_index() + 1
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
    assert sub_mute_qc.store == store0
    assert sub_mute_qc.translation_project == store0.translation_project
    assert sub_mute_qc.revision == unit.revision
    assert sub_mute_qc.type == SubmissionTypes.MUTE_CHECK
    assert sub_mute_qc.field == SubmissionFields.NONE
    assert sub_mute_qc.new_value == ""
    assert sub_mute_qc.old_value == ""
    assert not sub_mute_qc.pk


@pytest.mark.django_db
def test_unit_lifecycle_unmute_qc(store0, member):
    unit = store0.UnitClass()
    unit.store = store0
    unit.source_f = multistring("Foo")
    unit.index = store0.max_index() + 1
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
    assert sub_unmute_qc.store == store0
    assert sub_unmute_qc.translation_project == store0.translation_project
    assert sub_unmute_qc.revision == unit.revision
    assert sub_unmute_qc.type == SubmissionTypes.UNMUTE_CHECK
    assert sub_unmute_qc.field == SubmissionFields.NONE
    assert sub_unmute_qc.new_value == ""
    assert sub_unmute_qc.old_value == ""
    assert not sub_unmute_qc.pk


@pytest.mark.django_db
def test_unit_lifecycle_create_subs(store0, member):
    unit = store0.UnitClass()
    unit.store = store0
    unit.source_f = multistring("Foo")
    unit.index = store0.max_index() + 1
    unit.save()

    class DummyUnitLifecycle(UnitLifecycle):

        def sub_foo(self, **kwargs):
            self._called_foo = kwargs

        def sub_bar(self, **kwargs):
            self._called_bar = kwargs

    lc = DummyUnitLifecycle(unit)
    kwargs = dict(x=1, y=2)
    list(lc.create_subs(foo=kwargs))
    assert lc._called_foo == kwargs
    list(lc.create_subs(bar=kwargs))
    assert lc._called_bar == kwargs

    with pytest.raises(AttributeError):
        lc.update(baz=kwargs)


@pytest.mark.django_db
def test_unit_lifecycle_update(store0, member):
    unit = store0.UnitClass()
    unit.store = store0
    unit.source_f = multistring("Foo")
    unit.index = store0.max_index() + 1
    unit.save()

    class DummyUnitLifecycle(UnitLifecycle):

        def save_subs(self, subs):
            self._called_save = subs

        def create_subs(self, **kwargs):
            self._called_create = kwargs
            return [kwargs]

    lc = DummyUnitLifecycle(unit)
    kwargs = dict(x=1, y=2)
    lc.update(**kwargs)
    assert lc._called_create == kwargs
    assert lc._called_save == [kwargs]
