# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging

from django.contrib.auth import get_user_model
from django.utils.functional import cached_property

from pootle.core.delegate import frozen, review, versioned
from pootle.core.models import Revision
from pootle_store.contextmanagers import update_store_after

from .constants import OBSOLETE, PARSED, POOTLE_WINS
from .diff import StoreDiff
from .models import Suggestion
from .util import get_change_str


logger = logging.getLogger(__name__)


class StoreUpdate(object):
    """Wraps either a db or file store with instructions for updating
    a target db store
    """

    def __init__(self, source_store, target_store, **kwargs):
        self.source_store = source_store
        self.target_store = target_store
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

    @property
    def versioned_store(self):
        return versioned.get(
            self.target_store.__class__)(self.target_store)

    @cached_property
    def last_sync_store(self):
        return self.versioned_store.at_revision(
            self.store_revision or 0)


class UnitUpdater(object):
    """Updates a unit from a source with configuration"""

    def __init__(self, db_unit, update):
        self.db_unit = db_unit
        self.update = update
        self.original = frozen.get(db_unit.__class__)(db_unit)
        self.original_submitter = (
            db_unit.changed and db_unit.change.submitted_by)

    @cached_property
    def old_unit(self):
        return self.update.last_sync_store.findid(
            self.db_unit.getid())

    @property
    def uid(self):
        return self.db_unit.getid()

    @cached_property
    def newunit(self):
        return self.update.find_source_unit(self.uid)

    @cached_property
    def db_comment_updated(self):
        if not self.old_unit:
            return True
        return (self.db_unit.translator_comment or ""
                != self.old_unit.getnotes(origin="translator"))

    @cached_property
    def db_state_updated(self):
        if not self.old_unit:
            return True
        return not (
            self.db_unit.isfuzzy() == self.old_unit.isfuzzy()
            and self.db_unit.istranslated() == self.old_unit.istranslated()
            and self.db_unit.isobsolete() == self.old_unit.isobsolete())

    @cached_property
    def db_target_updated(self):
        if not self.old_unit:
            return True
        return self.db_unit.target != self.old_unit.target

    @cached_property
    def fs_comment_updated(self):
        if not self.old_unit and self.newunit:
            return True
        return (
            self.old_unit
            and self.newunit
            and (self.newunit.getnotes(origin="translator")
                 != self.old_unit.getnotes(origin="translator")))

    @cached_property
    def fs_state_updated(self):
        if not self.old_unit and self.newunit:
            return True
        return not (
            self.newunit.isfuzzy() == self.old_unit.isfuzzy()
            and self.newunit.istranslated() == self.old_unit.istranslated()
            and self.newunit.isobsolete() == self.old_unit.isobsolete())

    @cached_property
    def fs_target_updated(self):
        if not self.old_unit and self.newunit:
            return True
        return (
            self.newunit
            and self.newunit.target != self.old_unit.target)

    @cached_property
    def comment_conflict_found(self):
        return (
            self.fs_comment_updated
            and self.db_comment_updated)

    @cached_property
    def state_conflict_found(self):
        return (
            self.fs_state_updated
            and self.db_state_updated)

    @cached_property
    def target_conflict_found(self):
        return (
            self.fs_target_updated
            and self.db_target_updated
            and self.newunit.target != self.db_unit.target)

    @property
    def should_create_suggestion(self):
        return (
            self.update.suggest_on_conflict
            and self.target_conflict_found)

    @property
    def should_update_comment(self):
        return (
            self.newunit
            and self.fs_comment_updated
            and not (
                self.comment_conflict_found
                and self.update.resolve_conflict == POOTLE_WINS))

    @property
    def should_update_index(self):
        return (
            self.update.change_indices
            and self.uid in self.update.indices
            and self.db_unit.index != self.update.get_index(self.uid))

    @cached_property
    def should_update_source(self):
        return (
            self.newunit
            and (self.db_unit.source
                 != self.newunit.source))

    @property
    def should_update_state(self):
        return (
            self.newunit
            and self.fs_state_updated
            and not (
                self.db_target_updated
                and not self.should_update_target)
            and not (
                self.state_conflict_found
                and self.update.resolve_conflict == POOTLE_WINS))

    @property
    def should_update_target(self):
        return (
            self.newunit
            and self.fs_target_updated
            and self.newunit.target != self.db_unit.target
            and not (
                self.target_conflict_found
                and self.update.resolve_conflict == POOTLE_WINS))

    @property
    def should_unobsolete(self):
        return (
            self.newunit
            and self.resurrected
            and self.update.store_revision is not None
            and not (
                self.db_unit.revision > self.update.store_revision
                and self.update.resolve_conflict == POOTLE_WINS))

    @cached_property
    def resurrected(self):
        return (
            self.newunit
            and not self.newunit.isobsolete()
            and self.db_unit.isobsolete())

    def create_suggestion(self):
        suggestion_review = review.get(Suggestion)()
        return bool(
            suggestion_review.add(
                self.db_unit,
                self.newunit.target,
                self.update.user)[1]
            if self.update.resolve_conflict == POOTLE_WINS
            else suggestion_review.add(
                self.db_unit,
                self.original.target,
                self.original_submitter)[1])

    def save_unit(self):
        self.db_unit.revision = self.update.update_revision
        self.db_unit.save(
            user=self.update.user,
            changed_with=self.update.submission_type)

    def update_unit(self):
        reordered = False
        suggested = False
        updated = False
        need_update = (
            self.should_unobsolete
            or self.should_update_target
            or self.should_update_source
            or self.should_update_state
            or self.should_update_comment)
        if need_update:
            updated = self.db_unit.update(
                self.newunit, user=self.update.user)
        if self.should_update_index:
            self.db_unit.index = self.update.get_index(self.uid)
            reordered = True
            if not updated:
                self.db_unit.save(user=self.update.user)
        if self.should_create_suggestion:
            suggested = self.create_suggestion()
        if updated:
            self.save_unit()
        return (updated or reordered), suggested


class StoreUpdater(object):

    unit_updater_class = UnitUpdater

    def __init__(self, target_store):
        self.target_store = target_store

    def increment_unsynced_unit_revision(self, store_revision, update_revision):
        filter_by = {
            'revision__gt': store_revision or 0,
            'revision__lt': update_revision,
            'state__gt': OBSOLETE}
        return self.target_store.unit_set.filter(
            **filter_by).update(
                revision=Revision.incr())

    def units(self, uids):
        unit_set = self.target_store.unit_set.select_related(
            "change", "change__submitted_by")
        for unit in self.target_store.findid_bulk(uids, unit_set):
            unit.store = self.target_store
            yield unit

    def update(self, *args, **kwargs):
        with update_store_after(self.target_store):
            return self._update(*args, **kwargs)

    def _update(self, store, user=None, store_revision=None,
                submission_type=None, resolve_conflict=POOTLE_WINS,
                allow_add_and_obsolete=True):
        old_state = self.target_store.state

        if user is None:
            User = get_user_model()
            user = User.objects.get_system_user()

        update_revision = None
        changes = {}
        try:
            diff = StoreDiff(self.target_store, store, store_revision).diff()
            if diff is not None:
                update_revision = Revision.incr()
                changes = self.update_from_diff(
                    store,
                    store_revision,
                    diff, update_revision,
                    user, submission_type,
                    resolve_conflict,
                    allow_add_and_obsolete)
        finally:
            if old_state < PARSED:
                self.target_store.state = PARSED
                self.target_store.save()
            has_changed = any(x > 0 for x in changes.values())
            if has_changed:
                logger.info(
                    u"[update] %s units in %s [revision: %d]",
                    get_change_str(changes),
                    self.target_store.pootle_path,
                    (self.target_store.data.max_unit_revision or 0))
        return update_revision, changes

    def mark_units_obsolete(self, uids_to_obsolete, update):
        """Marks a bulk of units as obsolete.

        :param uids_to_obsolete: UIDs of the units to be marked as obsolete.
        :return: The number of units marked as obsolete.
        """
        obsoleted = 0
        old_store = update.last_sync_store
        for unit in self.target_store.findid_bulk(uids_to_obsolete):
            # Use the same (parent) object since units will
            # accumulate the list of cache attributes to clear
            # in the parent Store object
            added_since_sync = not bool(old_store.findid(unit.getid()))
            pootle_wins = (
                (unit.revision > update.store_revision or 0)
                and update.resolve_conflict == POOTLE_WINS)
            if added_since_sync or pootle_wins:
                continue
            unit.store = self.target_store
            if not unit.isobsolete():
                unit.makeobsolete()
                unit.revision = update.update_revision
                unit.save(user=update.user)
                obsoleted += 1
        return obsoleted

    def update_from_diff(self, store, store_revision,
                         to_change, update_revision, user,
                         submission_type, resolve_conflict=POOTLE_WINS,
                         allow_add_and_obsolete=True):
        changes = {}
        update_dbids, uid_index_map = to_change['update']
        update = StoreUpdate(
            store,
            self.target_store,
            user=user,
            submission_type=submission_type,
            resolve_conflict=resolve_conflict,
            change_indices=allow_add_and_obsolete,
            uids=update_dbids,
            indices=uid_index_map,
            store_revision=store_revision,
            update_revision=update_revision)

        if resolve_conflict == POOTLE_WINS:
            to_change["obsolete"] = [
                x for x
                in to_change["obsolete"]
                if x not in to_change["update"][0]]

        if allow_add_and_obsolete:
            # Update indexes
            for start, delta in to_change["index"]:
                self.target_store.update_index(start=start, delta=delta)

            # Add new units
            for unit, new_unit_index in to_change["add"]:
                self.target_store.addunit(
                    unit,
                    new_unit_index,
                    user=user,
                    changed_with=submission_type,
                    update_revision=update_revision)
            changes["added"] = len(to_change["add"])

            # Obsolete units
            changes["obsoleted"] = self.mark_units_obsolete(
                to_change["obsolete"], update)

        # Update units
        changes['updated'], changes['suggested'] = self.update_units(update)
        self.increment_unsynced_unit_revision(
            update.store_revision, update.update_revision)
        return changes

    def update_units(self, update):
        update_count = 0
        suggestion_count = 0
        if not update.uids:
            return update_count, suggestion_count
        for unit in self.units(update.uids):
            updated, suggested = self.unit_updater_class(
                unit,
                update).update_unit()
            if updated:
                update_count += 1
            if suggested:
                suggestion_count += 1
        return update_count, suggestion_count
