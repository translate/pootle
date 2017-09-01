# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os
from collections import namedtuple

from translate.storage.factory import getclass

from django.utils.functional import cached_property

from pootle.core.delegate import format_classes

from .models import Unit


logger = logging.getLogger(__name__)


class UnitSyncer(object):

    def __init__(self, unit, raw=False):
        self.unit = unit
        self.raw = raw

    @property
    def context(self):
        return self.unit.getcontext()

    @property
    def developer_notes(self):
        return self.unit.getnotes(origin="developer")

    @property
    def isfuzzy(self):
        return self.unit.isfuzzy()

    @property
    def isobsolete(self):
        return self.unit.isobsolete()

    @property
    def locations(self):
        return self.unit.getlocations()

    @property
    def source(self):
        return self.unit.source

    @property
    def target(self):
        return self.unit.target

    @property
    def translator_notes(self):
        return self.unit.getnotes(origin="translator")

    @property
    def unitid(self):
        return self.unit.getid()

    @property
    def unit_class(self):
        return self.unit.store.syncer.unit_class

    def convert(self, unitclass=None):
        newunit = self.create_unit(
            unitclass or self.unit_class)
        self.set_target(newunit)
        self.set_fuzzy(newunit)
        self.set_locations(newunit)
        self.set_developer_notes(newunit)
        self.set_translator_notes(newunit)
        self.set_unitid(newunit)
        self.set_context(newunit)
        self.set_obsolete(newunit)
        return newunit

    def create_unit(self, unitclass):
        return unitclass(self.source)

    def set_context(self, newunit):
        newunit.setcontext(self.context)

    def set_developer_notes(self, newunit):
        notes = self.developer_notes
        if notes:
            newunit.addnote(notes, origin="developer")

    def set_fuzzy(self, newunit):
        newunit.markfuzzy(self.isfuzzy)

    def set_locations(self, newunit):
        locations = self.locations
        if locations:
            newunit.addlocations(locations)

    def set_obsolete(self, newunit):
        if self.isobsolete:
            newunit.makeobsolete()

    def set_target(self, newunit):
        newunit.target = self.target

    def set_translator_notes(self, newunit):
        notes = self.translator_notes
        if notes:
            newunit.addnote(notes, origin="translator")

    def set_unitid(self, newunit):
        newunit.setid(self.unitid)


class StoreSyncer(object):
    unit_sync_class = UnitSyncer

    def __init__(self, store):
        self.store = store

    @property
    def translation_project(self):
        return self.store.translation_project

    @property
    def language(self):
        return self.translation_project.language

    @property
    def project(self):
        return self.translation_project.project

    @property
    def source_language(self):
        return self.project.source_language

    @property
    def unit_class(self):
        return self.file_class.UnitClass

    @cached_property
    def file_class(self):
        # get a plugin adapted file_class
        fileclass = format_classes.gather().get(
            str(self.store.filetype.extension))
        if fileclass:
            return fileclass
        if self.store.is_template:
            # namedtuple is equiv here of object() with name attr
            return self._getclass(
                namedtuple("instance", "name")(
                    name=".".join(
                        [os.path.splitext(self.store.name)[0],
                         str(self.store.filetype.extension)])))
        return self._getclass(self.store)

    def convert(self, fileclass=None, include_obsolete=False, raw=False):
        """export to fileclass"""
        fileclass = fileclass or self.file_class
        logger.debug(
            u"[sync] Converting: %s to %s",
            self.store.pootle_path,
            fileclass)
        output = fileclass()
        output.settargetlanguage(self.language.code)
        # FIXME: we should add some headers
        units = (
            self.store.unit_set
            if include_obsolete
            else self.store.units)
        for unit in units.iterator():
            output.addunit(
                self.unit_sync_class(unit, raw=raw).convert(output.UnitClass))
        return output

    def _getclass(self, obj):
        try:
            return getclass(obj)
        except ValueError:
            raise ValueError(
                "Unable to find conversion class for Store '%s'"
                % self.store.name)

    def get_new_units(self, old_ids, new_ids):
        return self.store.findid_bulk(
            [self.dbid_index.get(uid)
             for uid
             in new_ids - old_ids])

    def get_units_to_obsolete(self, disk_store, old_ids, new_ids):
        for uid in old_ids - new_ids:
            unit = disk_store.findid(uid)
            if unit and not unit.isobsolete():
                yield unit

    def obsolete_unit(self, unit, conservative):
        deleted = not unit.istranslated()
        obsoleted = (
            not deleted
            and not conservative)
        if obsoleted:
            unit.makeobsolete()
            deleted = not unit.isobsolete()
        if deleted:
            del unit
        return obsoleted, deleted

    def update_structure(self, disk_store, obsolete_units, new_units, conservative):
        obsolete = 0
        deleted = 0
        added = 0
        for unit in obsolete_units:
            _obsolete, _deleted = self.obsolete_unit(unit, conservative)
            if _obsolete:
                obsolete += 1
            if _deleted:
                deleted += 1
        for unit in new_units:
            newunit = unit.convert(disk_store.UnitClass)
            disk_store.addunit(newunit)
            added += 1
        return obsolete, deleted, added

    @cached_property
    def dbid_index(self):
        """build a quick mapping index between unit ids and database ids"""
        return dict(
            self.store.unit_set.live().values_list('unitid', 'id'))

    def sync(self, disk_store, last_revision,
             update_structure=False, conservative=True):
        logger.debug(u"[sync] Syncing: %s", self.store.pootle_path)
        old_ids = set(disk_store.getids())
        new_ids = set(self.dbid_index.keys())
        file_changed = False
        changes = {}
        if update_structure:
            obsolete_units = self.get_units_to_obsolete(
                disk_store, old_ids, new_ids)
            new_units = self.get_new_units(old_ids, new_ids)
            if obsolete_units or new_units:
                file_changed = True
                (changes['obsolete'],
                 changes['deleted'],
                 changes['added']) = self.update_structure(
                     disk_store,
                     obsolete_units,
                     new_units,
                     conservative=conservative)
        changes["updated"] = self.sync_units(
            disk_store,
            self.get_common_units(
                set(self.dbid_index.get(uid)
                    for uid
                    in old_ids & new_ids),
                last_revision,
                conservative))
        return bool(file_changed or any(changes.values())), changes

    def get_revision_filters(self, last_revision):
        # Get units modified after last sync and before this sync started
        filter_by = {
            'revision__lte': last_revision,
            'store': self.store}
        # Sync all units if first sync
        if self.store.last_sync_revision is not None:
            filter_by.update({'revision__gt': self.store.last_sync_revision})
        return filter_by

    def get_modified_units(self, last_revision):
        return set(
            Unit.objects.filter(**self.get_revision_filters(last_revision))
                        .values_list('id', flat=True).distinct()
            if last_revision > self.store.last_sync_revision
            else [])

    def get_common_units(self, common_dbids, last_revision, conservative):
        if conservative:
            # Sync only modified units
            common_dbids &= self.get_modified_units(last_revision)
        return self.store.findid_bulk(list(common_dbids))

    def sync_units(self, disk_store, units):
        updated = 0
        for unit in units:
            match = disk_store.findid(unit.getid())
            if match is not None:
                changed = unit.sync(match, unitclass=self.unit_sync_class)
                if changed:
                    updated += 1
        return updated

    def update_store_header(self, disk_store, **kwargs_):
        disk_store.settargetlanguage(self.language.code)
        disk_store.setsourcelanguage(self.source_language.code)
