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

from pootle.core.contextmanagers import update_data_after
from pootle.core.delegate import review
from pootle.core.log import log
from pootle.core.models import Revision

from .constants import OBSOLETE, PARSED, POOTLE_WINS
from .diff import StoreDiff
from .models import Suggestion
from .util import get_change_str


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
            and self.uid in self.update.indices
            and self.unit.index != self.update.get_index(self.uid))

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
                self.original.submitter)[1])

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

    def increment_unsynced_unit_revision(self, update_revision):
        filter_by = {
            'revision__gt': self.target_store.last_sync_revision,
            'revision__lt': update_revision,
            'state__gt': OBSOLETE}
        units = self.target_store.unit_set.filter(**filter_by)
        count = units.count()
        if count:
            # we update after here to trigger a stats update
            # for the store after doing Unit.objects.update()
            with update_data_after(self.target_store):
                units.update(revision=Revision.incr())
        return count

    def units(self, uids):
        unit_set = self.target_store.unit_set.select_related("submitted_by")
        for unit in self.target_store.findid_bulk(uids, unit_set):
            unit.store = self.target_store
            yield unit

    def update(self, store, user=None, store_revision=None,
               submission_type=None, resolve_conflict=POOTLE_WINS,
               allow_add_and_obsolete=True):
        logging.debug(u"Updating %s", self.target_store.pootle_path)
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
            else:
                self.target_store.state = old_state
            has_changed = any(x > 0 for x in changes.values())
            self.target_store.save()
            if has_changed:
                log(u"[update] %s units in %s [revision: %d]"
                    % (get_change_str(changes),
                       self.target_store.pootle_path,
                       (self.target_store.data.max_unit_revision or 0)))
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
            with update_data_after(self.target_store):
                for unit, new_unit_index in to_change["add"]:
                    self.target_store.addunit(
                        unit, new_unit_index, user=user,
                        update_revision=update_revision)
            changes["added"] = len(to_change["add"])

            # Obsolete units
            changes["obsoleted"] = self.target_store.mark_units_obsolete(
                to_change["obsolete"],
                update_revision)

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
        self.target_store.file_mtime = self.target_store.get_file_mtime()

        # update last_sync_revision if anything changed
        changed = changes and any(x > 0 for x in changes.values())
        if changed:
            update_unsynced = None
            if self.target_store.last_sync_revision is not None:
                update_unsynced = self.increment_unsynced_unit_revision(
                    update_revision)
            self.target_store.last_sync_revision = update_revision
            if update_unsynced:
                logging.info(u"[update] unsynced %d units in %s "
                             "[revision: %d]", update_unsynced,
                             self.target_store.pootle_path, update_revision)
        self.target_store.save()
        return changed

    def update_units(self, update):
        update_count = 0
        suggestion_count = 0
        if not update.uids:
            return update_count, suggestion_count
        with update_data_after(self.target_store):
            for unit in self.units(update.uids):
                updated, suggested = self.unit_updater_class(
                    unit, update).update_unit()
                if updated:
                    update_count += 1
                if suggested:
                    suggestion_count += 1
        return update_count, suggestion_count
