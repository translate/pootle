# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from translate.misc.multistring import multistring

from pootle_store.constants import FUZZY, UNTRANSLATED
from pootle_store.diff import DiffableStore
from pootle_store.syncer import StoreSyncer, UnitSyncer


class LangUnitSyncer(UnitSyncer):

    @property
    def target(self):
        if self.isfuzzy and not self.raw:
            return multistring("")
        return self.unit.target


class LangStoreSyncer(StoreSyncer):
    unit_sync_class = LangUnitSyncer


class DiffableLangStore(DiffableStore):

    def get_unit_state(self, file_unit):
        return (
            FUZZY
            if (file_unit["unitid"] in self.target_units
                and self.target_units[file_unit["unitid"]]["state"] == FUZZY
                and file_unit["state"] == UNTRANSLATED)
            else file_unit["state"])

    def get_unit_target(self, file_unit):
        return (
            self.target_units[file_unit["unitid"]]["target_f"]
            if file_unit["state"] == FUZZY
            else file_unit["target"])

    def get_file_unit(self, unit):
        file_unit = super(DiffableLangStore, self).get_file_unit(unit)
        file_unit["state"] = self.get_unit_state(file_unit)
        file_unit["target"] = self.get_unit_target(file_unit)
        return file_unit
