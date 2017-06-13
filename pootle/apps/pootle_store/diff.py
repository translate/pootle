# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import difflib
import logging
from collections import OrderedDict

from django.db import models
from django.utils.functional import cached_property

from pootle.core.delegate import format_diffs

from .constants import FUZZY, OBSOLETE, TRANSLATED, UNTRANSLATED
from .fields import to_python as multistring_to_python
from .unit import UnitProxy


logger = logging.getLogger(__name__)


class UnitDiffProxy(UnitProxy):
    """Wraps File/DB Unit dicts used by StoreDiff for equality comparison"""

    match_attrs = ["context", "developer_comment", "locations",
                   "source", "state", "target", "translator_comment"]

    def __eq__(self, other):
        return all(getattr(self, k) == getattr(other, k)
                   for k in self.match_attrs)

    def __ne__(self, other):
        return not self == other

    def hasplural(self):
        return (
            self.source is not None
            and (len(self.source.strings) > 1
                 or getattr(self.source, "plural", None)))

    def getnotes(self, origin=None):
        return self.unit.get("%s_comment" % origin, "")

    def getcontext(self):
        return self.unit["context"]

    def isfuzzy(self):
        return self.unit["state"] == FUZZY

    def isobsolete(self):
        return self.unit["state"] == OBSOLETE

    def getid(self):
        return self.unit["unitid"]


class DBUnit(UnitDiffProxy):
    pass


class FileUnit(UnitDiffProxy):

    @property
    def locations(self):
        return "\n".join(self.unit["locations"])

    @property
    def source(self):
        return multistring_to_python(self.unit["source"])

    @property
    def target(self):
        return multistring_to_python(self.unit["target"])

    def hasplural(self):
        return self.unit["hasplural"]


class DiffableStore(object):
    """Default Store representation for diffing

    this can be customized per-format using `format_diffs` provider
    """

    file_unit_class = FileUnit
    db_unit_class = DBUnit

    unit_fields = (
        "unitid", "state", "id", "index", "revision",
        "source_f", "target_f", "developer_comment",
        "translator_comment", "locations", "context")

    def __init__(self, target_store, source_store):
        self.target_store = target_store
        self.source_store = source_store

    def get_db_units(self, unit_qs):
        diff_units = OrderedDict()
        units = unit_qs.values(*self.unit_fields).order_by("index")
        for unit in units:
            diff_units[unit["unitid"]] = unit
        return diff_units

    def get_file_unit(self, unit):
        state = UNTRANSLATED
        if unit.isobsolete():
            state = OBSOLETE
        elif unit.istranslated():
            state = TRANSLATED
        elif unit.isfuzzy():
            state = FUZZY
        return {
            "unitid": unit.getid(),
            "context": unit.getcontext(),
            "locations": unit.getlocations(),
            "source": unit.source,
            "target": unit.target,
            "state": state,
            "hasplural": unit.hasplural(),
            "developer_comment": unit.getnotes(origin="developer"),
            "translator_comment": unit.getnotes(origin="translator")}

    def get_file_units(self, units):
        diff_units = OrderedDict()
        for unit in units:
            if unit.isheader():
                continue
            if unit.getid() in diff_units:
                unitid = unit.getid()
                logger.warning(
                    "[diff] Duplicate unit found: %s %s",
                    self.target_store.name,
                    (unitid
                     if len(unitid) <= 20
                     else "%s..." % unitid[:17]))
            diff_units[unit.getid()] = self.get_file_unit(unit)
        return diff_units

    @cached_property
    def target_units(self):
        return self.get_db_units(self.target_store.unit_set)

    @cached_property
    def source_units(self):
        if isinstance(self.source_store, models.Model):
            return self.get_db_units(self.source_store.unit_set.live())
        return self.get_file_units(self.source_store.units)

    @property
    def target_unit_class(self):
        return self.db_unit_class

    @property
    def source_unit_class(self):
        if isinstance(self.source_store, models.Model):
            return self.db_unit_class
        return self.file_unit_class


class StoreDiff(object):
    """Compares 2 DBStores"""

    def __init__(self, target_store, source_store, source_revision):
        self.target_store = target_store
        self.source_store = source_store
        self.source_revision = source_revision
        self.target_revision = self.get_target_revision()

    @property
    def diff_class(self):
        diffs = format_diffs.gather()
        differ = diffs.get(
            self.target_store.filetype.name)
        if differ:
            return differ
        return diffs["default"]

    def get_target_revision(self):
        return self.target_store.data.max_unit_revision or 0

    @cached_property
    def active_target_units(self):
        return [unitid for unitid, unit in self.target_units.items()
                if unit['state'] != OBSOLETE]

    @cached_property
    def diffable(self):
        return self.diff_class(self.target_store, self.source_store)

    @cached_property
    def target_units(self):
        """All of the db units regardless of state or revision"""
        return self.diffable.target_units

    @cached_property
    def source_units(self):
        """All of the db units regardless of state or revision"""
        return self.diffable.source_units

    @cached_property
    def insert_points(self):
        """Returns a list of insert points with update index info.
        :return: a list of tuples
            ``(insert_at, uids_to_add, next_index, update_index_delta)`` where
            ``insert_at`` is the point for inserting
            ``uids_to_add`` are the units to be inserted
            ``update_index_delta`` is the offset for index updating
            ``next_index`` is the starting point after which
            ``update_index_delta`` should be applied.
        """
        inserts = []
        new_unitid_list = self.new_unit_list
        for (tag, i1, i2, j1, j2) in self.opcodes:
            if tag == 'insert':
                update_index_delta = 0
                insert_at = 0
                if i1 > 0:
                    insert_at = (
                        self.target_units[
                            self.active_target_units[i1 - 1]]['index'])
                next_index = insert_at + 1
                if i1 < len(self.active_target_units):
                    next_index = self.target_units[
                        self.active_target_units[i1]]["index"]
                    update_index_delta = (
                        j2 - j1 - next_index + insert_at + 1)

                inserts.append((insert_at,
                                new_unitid_list[j1:j2],
                                next_index,
                                update_index_delta))

            elif tag == 'replace':
                insert_at = self.target_units[
                    self.active_target_units[max(i1 - 1, 0)]]['index']
                next_index = self.target_units[
                    self.active_target_units[i2 - 1]]['index']
                inserts.append((insert_at,
                                new_unitid_list[j1:j2],
                                next_index,
                                j2 - j1 - insert_at + next_index))
        return inserts

    @cached_property
    def new_unit_list(self):
        # If source_revision is gte than the target_revision then new unit list
        # will be exactly what is in the file
        if self.source_revision >= self.target_revision:
            return self.source_units.keys()

        # These units are kept as they have been updated since source_revision
        # but do not appear in the file
        new_units = [u for u in self.updated_target_units
                     if u not in self.source_units]

        # These unit are either present in both or only in the file so are
        # kept in the file order
        new_units += [u for u in self.source_units.keys()
                      if u not in self.obsoleted_target_units]

        return new_units

    @cached_property
    def obsoleted_target_units(self):
        return [unitid for unitid, unit in self.target_units.items()
                if (unit['state'] == OBSOLETE
                    and unit["revision"] > self.source_revision)]

    @cached_property
    def opcodes(self):
        sm = difflib.SequenceMatcher(None,
                                     self.active_target_units,
                                     self.new_unit_list)
        return sm.get_opcodes()

    @cached_property
    def updated_target_units(self):
        return [unitid for unitid, unit in self.target_units.items()
                if (unit['revision'] > self.source_revision
                    and unit["state"] != OBSOLETE)]

    def diff(self):
        """Return a dictionary of change actions or None if there are no
        changes to be made.
        """
        diff = {"index": self.get_indexes_to_update(),
                "obsolete": self.get_units_to_obsolete(),
                "add": self.get_units_to_add(),
                "update": self.get_units_to_update()}
        if self.has_changes(diff):
            return diff
        return None

    def get_indexes_to_update(self):
        offset = 0
        index_updates = []
        for (insert_at_, uids_add_, next_index, delta) in self.insert_points:
            if delta > 0:
                index_updates += [(next_index + offset, delta)]
                offset += delta
        return index_updates

    def get_units_to_add(self):
        offset = 0
        to_add = []
        proxy = (
            isinstance(self.source_store, models.Model)
            and DBUnit or FileUnit)

        for (insert_at, uids_add, next_index_, delta) in self.insert_points:
            for index, uid in enumerate(uids_add):
                source_unit = self.source_units.get(uid)
                if source_unit and uid not in self.target_units:
                    new_unit_index = insert_at + index + 1 + offset
                    to_add += [(proxy(source_unit), new_unit_index)]
            if delta > 0:
                offset += delta
        return to_add

    def get_units_to_obsolete(self):
        return [unit['id'] for unitid, unit in self.target_units.items()
                if ((unitid not in self.source_units
                     or self.source_units[unitid]['state'] == OBSOLETE)
                    and unitid in self.active_target_units
                    and unitid not in self.updated_target_units)]

    def get_units_to_update(self):
        uid_index_map = {}
        offset = 0

        for (insert_at, uids_add, next_index_, delta) in self.insert_points:
            for index, uid in enumerate(uids_add):
                new_unit_index = insert_at + index + 1 + offset
                if uid in self.target_units:
                    uid_index_map[uid] = {
                        'dbid': self.target_units[uid]['id'],
                        'index': new_unit_index}
            if delta > 0:
                offset += delta
        update_ids = self.get_updated_sourceids()
        update_ids.update({x['dbid'] for x in uid_index_map.values()})
        return (update_ids, uid_index_map)

    def get_updated_sourceids(self):
        """Returns a set of unit DB ids to be updated.
        """
        update_ids = set()

        for (tag, i1, i2, j1_, j2_) in self.opcodes:
            if tag != 'equal':
                continue
            update_ids.update(
                set(self.target_units[uid]['id']
                    for uid in self.active_target_units[i1:i2]
                    if (uid in self.source_units
                        and (
                            self.diffable.target_unit_class(
                                self.target_units[uid])
                            != self.diffable.source_unit_class(
                                self.source_units[uid])))))
        return update_ids

    def has_changes(self, diff):
        for k, v in diff.items():
            if k == "update":
                if len(v[0]) > 0:
                    return True
            else:
                if len(v) > 0:
                    return True
        return False
