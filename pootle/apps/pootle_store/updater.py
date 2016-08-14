# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.utils import timezone
from django.utils.functional import cached_property

from pootle_store.constants import POOTLE_WINS


class StoreUpdate(object):
    """Wraps either a db or file store with instructions for updating
    a target db store
    """

    def __init__(self, source_store, **kwargs):
        self.source_store = source_store
        self.kwargs = kwargs

    def find_source_unit(self, uid):
        return self.source_store.findid(uid)

    def get_index(self, uid):
        return self.indices[uid]['index']

    @property
    def uids(self):
        return list(self.kwargs["uids"])

    @property
    def change_indices(self):
        return self.kwargs["change_indices"]

    @property
    def indices(self):
        return self.kwargs["indices"]

    @property
    def store_revision(self):
        return self.kwargs["store_revision"]

    @property
    def submission_type(self):
        return self.kwargs["submission_type"]

    @property
    def update_revision(self):
        return self.kwargs["update_revision"]

    @property
    def resolve_conflict(self):
        return self.kwargs["resolve_conflict"]

    @property
    def user(self):
        return self.kwargs["user"]

    @property
    def suggest_on_conflict(self):
        return self.kwargs.get("suggest_on_conflict", True)


class FrozenUnit(object):
    """Freeze unit vars for comparison"""

    def __init__(self, unit):
        self.target = unit.target_f
        self.state = unit.state
        self.submitter = unit.submitted_by
        self.translator_comment = unit.getnotes(origin="translator")


class UnitUpdater(object):
    """Updates a unit from a source with configuration"""

    def __init__(self, unit, update):
        self.unit = unit
        self.update = update
        self.original = FrozenUnit(unit)

    @property
    def translator_comment(self):
        return self.unit.getnotes(origin="translator")

    @property
    def translator_comment_updated(self):
        return (
            (self.original.translator_comment or self.translator_comment)
            and self.original.translator_comment != self.translator_comment)

    @cached_property
    def at(self):
        return timezone.now()

    @property
    def uid(self):
        return self.unit.getid()

    @cached_property
    def newunit(self):
        return self.update.find_source_unit(self.uid)

    @cached_property
    def conflict_found(self):
        return (
            self.newunit
            and self.update.store_revision is not None
            and self.update.store_revision < self.unit.revision
            and (self.unit.target != self.newunit.target
                 or self.unit.source != self.newunit.source))

    @property
    def should_create_suggestion(self):
        return (
            self.update.suggest_on_conflict
            and self.conflict_found)

    @property
    def should_update_index(self):
        return (
            self.update.change_indices
            and self.uid in self.update.indices)

    @property
    def should_update_target(self):
        return (
            self.newunit
            and not (self.conflict_found
                     and self.update.resolve_conflict == POOTLE_WINS))

    @property
    def target_updated(self):
        return self.unit.target != self.original.target

    def create_suggestion(self):
        return bool(
            self.unit.add_suggestion(self.newunit.target, self.update.user)[1]
            if self.update.resolve_conflict == POOTLE_WINS
            else self.unit.add_suggestion(
                self.original.target, self.original.submitter)[1])

    def record_submission(self):
        self.unit.store.record_submissions(
            self.unit,
            self.original.target,
            self.original.state,
            self.at,
            self.update.user,
            self.update.submission_type)

    def save_unit(self):
        self.unit.save(revision=self.update.update_revision)

    def set_commented(self):
        self.unit.commented_by = self.update.user
        self.unit.commented_on = self.at

    def set_submitted(self):
        self.unit.submitted_by = self.update.user
        self.unit.submitted_on = self.at
        self.unit.reviewed_on = None
        self.unit.reviewed_by = None

    def set_unit(self):
        self.record_submission()
        if self.translator_comment_updated:
            self.set_commented()
        if self.target_updated:
            self.set_submitted()
        self.save_unit()

    def update_unit(self):
        suggested = False
        updated = False
        if self.should_update_target:
            updated = self.unit.update(
                self.newunit, user=self.update.user)
        if self.should_update_index:
            self.unit.index = self.update.get_index(self.uid)
            updated = True
        if updated:
            self.set_unit()
        if self.should_create_suggestion:
            suggested = self.create_suggestion()
        return updated, suggested


class StoreUpdater(object):

    unit_updater_class = UnitUpdater

    def __init__(self, target_store):
        self.target_store = target_store

    def units(self, uids):
        for unit in self.target_store.findid_bulk(uids):
            unit.store = self.target_store
            yield unit

    def update(self, update):
        update_count = 0
        suggestion_count = 0
        for unit in self.units(update.uids):
            updated, suggested = self.unit_updater_class(
                unit, update).update_unit()
            if updated:
                update_count += 1
            if suggested:
                suggestion_count += 1
        return update_count, suggestion_count
