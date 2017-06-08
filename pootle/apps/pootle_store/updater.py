# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.functional import cached_property

from pootle.core.delegate import frozen, review
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


class UnitUpdater(object):
    """Updates a unit from a source with configuration"""

    def __init__(self, unit, update):
        self.unit = unit
        self.update = update
        self.original = frozen.get(unit.__class__)(unit)
        self.original_submitter = (
            unit.changed and unit.change.submitted_by)

    @property
    def translator_comment(self):
        comment = self.newunit.getnotes(origin="translator")
        return None if comment == '' else comment

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
            and (self.target_updated
                 or self.state_updated
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
            and self.uid in self.update.indices
            and self.unit.index != self.update.get_index(self.uid))

    @property
    def should_update_target(self):
        return (
            self.newunit
            and self.target_updated
            and not (
                self.conflict_found
                and self.update.resolve_conflict == POOTLE_WINS))

    @property
    def should_update_state(self):
        return (
            self.newunit
            and self.state_updated
            and not (
                self.conflict_found
                and self.update.resolve_conflict == POOTLE_WINS))

    @property
    def should_update_comment(self):
        return (
            self.newunit
            and self.translator_comment_updated
            and not (
                self.conflict_found
                and self.update.resolve_conflict == POOTLE_WINS))

    @cached_property
    def should_update_source(self):
        return (self.newunit
                and self.unit.source != self.newunit.source)

    @cached_property
    def resurrected(self):
        return (
            self.newunit
            and not self.newunit.isobsolete()
            and self.unit.isobsolete())

    @cached_property
    def state_updated(self):
        # `fuzzy` state change is checked here.
        # `translated` and `obsolete` states are handled separately.
        if not self.newunit:
            return False
        source_fuzzy = (
            self.newunit.isfuzzy()
            and not self.newunit.isobsolete())
        target_fuzzy = (
            self.unit.isfuzzy()
            and not self.unit.isobsolete())
        return source_fuzzy != target_fuzzy

    @cached_property
    def target_updated(self):
        if not self.update.store_revision:
            return True
        if self.unit.target == self.newunit.target:
            return False
        return True

    def create_suggestion(self):
        suggestion_review = review.get(Suggestion)()
        return bool(
            suggestion_review.add(
                self.unit,
                self.newunit.target,
                self.update.user)[1]
            if self.update.resolve_conflict == POOTLE_WINS
            else suggestion_review.add(
                self.unit,
                self.original.target,
                self.original_submitter)[1])

    def save_unit(self):
        self.unit.revision = self.update.update_revision
        self.unit.save(
            user=self.update.user,
            changed_with=self.update.submission_type)

    @property
    def should_unobsolete(self):
        return (
            self.newunit
            and self.resurrected
            and self.update.store_revision is not None
            and not (
                self.unit.revision > self.update.store_revision
                and self.update.resolve_conflict == POOTLE_WINS))

    def update_unit(self):
        reordered = False
        suggested = False
        updated = False
        need_update = (self.should_unobsolete
                       or self.should_update_target
                       or self.should_update_source
                       or self.should_update_state
                       or self.should_update_comment)
        if need_update:
            updated = self.unit.update(
                self.newunit, user=self.update.user)
        if self.should_update_index:
            self.unit.index = self.update.get_index(self.uid)
            reordered = True
            if not updated:
                self.unit.save(user=self.update.user)
        if updated:
            self.save_unit()
        if self.should_create_suggestion:
            suggested = self.create_suggestion()
        return (updated or reordered), suggested


class StoreUpdater(object):

    unit_updater_class = UnitUpdater

    def __init__(self, target_store):
        self.target_store = target_store

    def increment_unsynced_unit_revision(self, update_revision):
        filter_by = {
            'revision__gt': self.target_store.last_sync_revision,
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

    def update_from_diff(self, store, store_revision,
                         to_change, update_revision, user,
                         submission_type, resolve_conflict=POOTLE_WINS,
                         allow_add_and_obsolete=True):
        changes = {}

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
            changes["obsoleted"] = self.target_store.mark_units_obsolete(
                to_change["obsolete"],
                update_revision,
                user=user)

        # Update units
        update_dbids, uid_index_map = to_change['update']
        update = StoreUpdate(
            store,
            user=user,
            submission_type=submission_type,
            resolve_conflict=resolve_conflict,
            change_indices=allow_add_and_obsolete,
            uids=update_dbids,
            indices=uid_index_map,
            store_revision=store_revision,
            update_revision=update_revision)
        changes['updated'], changes['suggested'] = self.update_units(update)
        return changes

    def update_from_disk(self, overwrite=False):
        """Update DB with units from the disk Store.

        :param overwrite: make db match file regardless of last_sync_revision.
        """
        changed = False

        if not self.target_store.file:
            return changed

        if overwrite:
            store_revision = self.target_store.data.max_unit_revision
        else:
            store_revision = self.target_store.last_sync_revision or 0

        # update the units
        update_revision, changes = self.update(
            self.target_store.file.store,
            store_revision=store_revision)

        # update file_mtime
        file_changed = False
        file_mtime = self.target_store.get_file_mtime()
        if file_mtime != self.target_store.file_mtime:
            self.target_store.file_mtime = file_mtime
            file_changed = True

        # update last_sync_revision if anything changed
        changed = changes and any(x > 0 for x in changes.values())
        if changed:
            update_unsynced = None
            if self.target_store.last_sync_revision is not None:
                update_unsynced = self.increment_unsynced_unit_revision(
                    update_revision)
            self.target_store.last_sync_revision = update_revision
            if update_unsynced:
                logger.debug(
                    u"[update] Synced (no change): "
                    u"%d units in %s [revision: %d]",
                    update_unsynced,
                    self.target_store.pootle_path,
                    update_revision)
        if file_changed or changed:
            self.target_store.save()
        if "store" in self.target_store.file.__dict__:
            del self.target_store.file.__dict__["store"]
        return changed

    def update_units(self, update):
        update_count = 0
        suggestion_count = 0
        if not update.uids:
            return update_count, suggestion_count
        for unit in self.units(update.uids):
            updated, suggested = self.unit_updater_class(
                unit, update).update_unit()
            if updated:
                update_count += 1
            if suggested:
                suggestion_count += 1
        return update_count, suggestion_count
