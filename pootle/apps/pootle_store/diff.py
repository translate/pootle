# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import difflib
from collections import OrderedDict

from django.utils.functional import cached_property

from .fields import to_python as multistring_to_python
from .unit import UnitProxy
from .util import FUZZY, OBSOLETE, TRANSLATED, UNTRANSLATED


class UnitDiffProxy(UnitProxy):
    """Wraps File/DB Unit dicts used by StoreDiff for equality comparison"""

    match_attrs = ["context", "developer_comment", "locations",
                   "source", "state", "target", "translator_comment"]

    def __eq__(self, other):
        return all(getattr(self, k) == getattr(other, k)
                   for k in self.match_attrs)

    def __ne__(self, other):
        return not self == other


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


class StoreDiff(object):

    def __init__(self, db_store, file_store, file_revision):
        self.db_store = db_store
        self.file_store = file_store
        self.db_revision = db_store.get_max_unit_revision()
        self.file_revision = file_revision

    @cached_property
    def active_units(self):
        return [unitid for unitid, unit in self.db_units.items()
                if unit['state'] != OBSOLETE]

    @cached_property
    def db_units(self):
        """All of the db units regardless of state or revision"""
        db_units = OrderedDict()
        unit_fields = ("unitid", "state", "id", "index", "revision",
                       "source_f", "target_f", "developer_comment",
                       "translator_comment", "locations", "context")
        for unit in self.db_store.unit_set.values(*unit_fields).order_by("index"):
            db_units[unit["unitid"]] = unit
        return db_units

    @cached_property
    def file_units(self):
        file_units = OrderedDict()
        for unit in self.file_store.units:
            if unit.isheader():
                continue
            state = UNTRANSLATED
            if unit.isobsolete():
                state = OBSOLETE
            elif unit.istranslated():
                state = TRANSLATED
            elif unit.isfuzzy():
                state = FUZZY
            file_units[unit.getid()] = {
                "unitid": unit.getid(),
                "context": unit.getcontext(),
                "locations": unit.getlocations(),
                "source": unit.source,
                "target": unit.target,
                "state": state,
                "developer_comment": unit.getnotes(origin="developer"),
                "translator_comment": unit.getnotes(origin="translator")}
        return file_units

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
                        self.db_units[self.active_units[i1 - 1]]['index'])
                next_index = insert_at + 1
                if i1 < len(self.active_units):
                    next_index = self.db_units[self.active_units[i1]]["index"]
                    update_index_delta = (
                        j2 - j1 - next_index + insert_at + 1)

                inserts.append((insert_at,
                                new_unitid_list[j1:j2],
                                next_index,
                                update_index_delta))

            elif tag == 'replace':
                insert_at = self.db_units[self.active_units[i1 - 1]]['index']
                next_index = self.db_units[self.active_units[i2 - 1]]['index']
                inserts.append((insert_at,
                                new_unitid_list[j1:j2],
                                next_index,
                                j2 - j1 - insert_at + next_index))

        return inserts

    @cached_property
    def new_unit_list(self):
        # If file_revision is gte than the db_revision then new unit list
        # will be exactly what is in the file
        if self.file_revision >= self.db_revision:
            return self.file_units.keys()

        # These units are kept as they have been updated since file_revision
        # but do not appear in the file
        new_units = [u for u in self.updated_db_units
                     if u not in self.file_units]

        # These unit are either present in both or only in the file so are
        # kept in the file order
        new_units += [u for u in self.file_units.keys()
                      if u not in self.obsoleted_db_units]

        return new_units

    @cached_property
    def obsoleted_db_units(self):
        return [unitid for unitid, unit in self.db_units.items()
                if (unit['state'] == OBSOLETE
                    and unit["revision"] > self.file_revision)]

    @cached_property
    def opcodes(self):
        sm = difflib.SequenceMatcher(None,
                                     self.active_units,
                                     self.new_unit_list)
        return sm.get_opcodes()

    @cached_property
    def updated_db_units(self):
        return [unitid for unitid, unit in self.db_units.items()
                if (unit['revision'] > self.file_revision
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
        for (insert_at, uids_add, next_index, delta) in self.insert_points:
            if delta > 0:
                index_updates += [(next_index + offset, delta)]
                offset += delta
        return index_updates

    def get_units_to_add(self):
        offset = 0
        to_add = []
        for (insert_at, uids_add, next_index, delta) in self.insert_points:
            for index, uid in enumerate(uids_add):
                file_unit = self.file_store.findid(uid)
                if file_unit and file_unit.getid() not in self.db_units:
                    new_unit_index = insert_at + index + 1 + offset
                    to_add += [(file_unit, new_unit_index)]
            if delta > 0:
                offset += delta
        return to_add

    def get_units_to_obsolete(self):
        return [unit['id'] for unitid, unit in self.db_units.items()
                if (unitid not in self.file_units
                    and unitid in self.active_units
                    and unitid not in self.updated_db_units)]

    def get_units_to_update(self):
        uid_index_map = {}
        offset = 0

        for (insert_at, uids_add, next_index, delta) in self.insert_points:
            for index, uid in enumerate(uids_add):
                new_unit_index = insert_at + index + 1 + offset
                if uid in self.db_units:
                    uid_index_map[uid] = {
                        'dbid': self.db_units[uid]['id'],
                        'index': new_unit_index}
            if delta > 0:
                offset += delta
        update_dbids = self.get_updated_dbids()
        update_dbids.update({x['dbid'] for x in uid_index_map.values()})
        return (update_dbids, uid_index_map)

    def get_updated_dbids(self):
        """Returns a set of unit DB ids to be updated.
        """
        update_dbids = set()

        for (tag, i1, i2, j1, j2) in self.opcodes:
            if tag == 'equal':
                update_dbids.update(
                    set(self.db_units[uid]['id']
                        for uid in self.active_units[i1:i2]
                        if (uid in self.file_units
                            and (DBUnit(self.db_units[uid])
                                 != FileUnit(self.file_units[uid])))))
        return update_dbids

    def has_changes(self, diff):
        for k, v in diff.items():
            if k == "update":
                if len(v[0]) > 0:
                    return True
            else:
                if len(v) > 0:
                    return True
        return False
