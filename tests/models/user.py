#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

import accounts
from pootle_store.util import FUZZY, TRANSLATED

from tests.fixtures.models.store import (TEST_EVIL_UPDATE_PO,
                                         _create_submission_and_suggestion,
                                         _create_comment_on_unit)


def _make_evil_member_updates(store, evil_member):
    # evil_member makes following changes:
    #   - rejects member's suggestion on unit
    #   - changes unit
    #   - adds another suggestion on unit
    #   - accepts their own suggestion
    #   - adds a comment on unit
    #   - adds another unit
    member_suggestion = store.units[0].get_suggestions().first()
    unit = store.units[0]
    unit.reject_suggestion(member_suggestion,
                           store.units[0].store.translation_project,
                           evil_member)
    _create_submission_and_suggestion(store,
                                      evil_member,
                                      filename=TEST_EVIL_UPDATE_PO,
                                      suggestion="EVIL SUGGESTION")
    evil_suggestion = store.units[0].get_suggestions().first()
    store.units[0].accept_suggestion(evil_suggestion,
                                     store.units[0].store.translation_project,
                                     evil_member)
    _create_comment_on_unit(store.units[0], evil_member, "EVIL COMMENT")


def _test_user_merged(unit, src_user, target_user):
    # TODO: test reviews and comments
    if src_user.id:
        assert src_user.submitted.count() == 0
        assert src_user.suggestions.count() == 0

    assert target_user.submitted.first() == unit
    assert target_user.suggestions.first() == unit.get_suggestions().first()


def _test_before_evil_user_updated(store, member, teststate=False):
    unit = store.units[0]

    # Unit state is fuzzy
    assert unit.state == FUZZY

    # Unit target was updated.
    assert unit.target_f == "Hello, world UPDATED"
    assert unit.submitted_by == member

    # But member also added a suggestion to the unit.
    assert unit.get_suggestions().count() == 1
    assert unit.get_suggestions().first().user == member

    # And added a comment on the unit.
    assert unit.translator_comment == "NICE COMMENT"
    assert unit.commented_by == member

    # Only 1 unit round here.
    assert store.units.count() == 1


def _test_after_evil_user_updated(store, evil_member):
    unit = store.units[0]

    # Unit state is TRANSLATED
    assert unit.state == TRANSLATED

    # Evil member has accepted their own suggestion.
    assert unit.target_f == "EVIL SUGGESTION"
    assert unit.submitted_by == evil_member

    # And rejected member's.
    assert unit.get_suggestions().count() == 0

    # And added their own comment.
    assert unit.translator_comment == "EVIL COMMENT"
    assert unit.commented_by == evil_member

    # Evil member has added another unit.
    assert store.units.count() == 2
    assert store.units[1].target_f == "Goodbye, world EVIL"
    assert store.units[1].submitted_by == evil_member


def _test_user_purging(store, member, evil_member, purge):

    first_revision = store.get_max_unit_revision()
    unit = store.units[0]

    # Get intitial change times
    initial_submission_time = unit.submitted_on
    initial_comment_time = unit.commented_on
    initial_review_time = unit.reviewed_on

    # Test state before evil user has updated.
    _test_before_evil_user_updated(store, member, True)

    # Update as evil member
    _make_evil_member_updates(store, evil_member)

    # Revision has increased
    latest_revision = store.get_max_unit_revision()
    assert latest_revision > first_revision

    unit = store.units[0]

    # Test submitted/commented/reviewed times on the unit
    # This is an unreliable test on mysql due to datetime precision
    if unit.submitted_on.time().microsecond != 0:

        # Times have changed
        assert unit.submitted_on != initial_submission_time
        assert unit.commented_on != initial_comment_time
        assert unit.reviewed_on != initial_review_time

    # Test state after evil user has updated.
    _test_after_evil_user_updated(store, evil_member)

    # Purge evil_member
    purge(evil_member)

    # Revision has increased again.
    assert store.get_max_unit_revision() > latest_revision

    unit = store.units[0]

    # Times are back to previous times - by any precision
    assert unit.submitted_on == initial_submission_time
    assert unit.commented_on == initial_comment_time
    assert unit.reviewed_on == initial_review_time

    # State is be back to how it was before evil user updated.
    _test_before_evil_user_updated(store, member)


@pytest.mark.django_db
def test_merge_user(en_tutorial_po, member, member2):
    """Test merging user to another user."""
    unit = _create_submission_and_suggestion(en_tutorial_po, member)
    accounts.utils.UserMerger(member, member2).merge()
    _test_user_merged(unit, member, member2)


@pytest.mark.django_db
def test_delete_user(en_tutorial_po, member, nobody):
    """Test default behaviour of User.delete - merge to nobody"""
    unit = _create_submission_and_suggestion(en_tutorial_po, member)
    member.delete()
    _test_user_merged(unit, member, nobody)


@pytest.mark.django_db
def test_purge_user(en_tutorial_po_member_updated,
                    member, evil_member):
    """Test purging user using `purge_user` function"""
    _test_user_purging(en_tutorial_po_member_updated,
                       member, evil_member,
                       lambda m: accounts.utils.UserPurger(m).purge())


@pytest.mark.django_db
def test_delete_purge_user(en_tutorial_po_member_updated,
                           member, evil_member):
    """Test purging user using `User.delete(purge=True)`"""
    _test_user_purging(en_tutorial_po_member_updated,
                       member, evil_member,
                       lambda m: m.delete(purge=True))
