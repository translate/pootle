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
from pootle.core.log import log
from pootle.core.url_helpers import split_pootle_path

from .models import Unit
from .util import get_change_str


class UnitSyncer(object):

    def __init__(self, unit):
        self.unit = unit

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

    @cached_property
    def disk_store(self):
        return self.store.file.store

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
    def store_file_path(self):
        return os.path.join(
            self.translation_project.abs_real_path,
            *split_pootle_path(self.store.pootle_path)[2:])

    @property
    def relative_file_path(self):
        path_parts = split_pootle_path(self.store.pootle_path)
        path_prefix = [path_parts[1]]
        if self.project.get_treestyle() != "gnu":
            path_prefix.append(path_parts[0])
        return os.path.join(*(path_prefix + list(path_parts[2:])))

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

    def convert(self, fileclass=None):
        """export to fileclass"""
        fileclass = fileclass or self.file_class
        logging.debug(
            u"Converting %s to %s",
            self.store.pootle_path,
            fileclass)
        output = fileclass()
        output.settargetlanguage(self.language.code)
        # FIXME: we should add some headers
        for unit in self.store.units.iterator():
            output.addunit(
                self.unit_sync_class(unit).convert(output.UnitClass))
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

    def get_units_to_obsolete(self, old_ids, new_ids):
        for uid in old_ids - new_ids:
            unit = self.disk_store.findid(uid)
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

    def update_structure(self, obsolete_units, new_units, conservative):
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
            newunit = unit.convert(self.disk_store.UnitClass)
            self.disk_store.addunit(newunit)
            added += 1
        return obsolete, deleted, added

    def create_store_file(self, last_revision, user):
        logging.debug(u"Creating file %s", self.store.pootle_path)
        store = self.convert()
        if not os.path.exists(os.path.dirname(self.store_file_path)):
            os.makedirs(os.path.dirname(self.store_file_path))
        self.store.file = self.relative_file_path
        store.savefile(self.store_file_path)
        log(u"Created file for %s [revision: %d]" %
            (self.store.pootle_path, last_revision))
        self.update_store_header(user=user)
        self.store.file.savestore()
        self.store.file_mtime = self.store.get_file_mtime()
        self.store.last_sync_revision = last_revision
        self.store.save()

    def update_newer(self, last_revision):
        return (
            not self.store.file.exists()
            or last_revision > self.store.last_sync_revision
        )

    @cached_property
    def dbid_index(self):
        """build a quick mapping index between unit ids and database ids"""
        return dict(
            self.store.unit_set.live().values_list('unitid', 'id'))

    def sync(self, update_structure=False, conservative=True,
             user=None, only_newer=True):
        last_revision = self.store.data.max_unit_revision

        # TODO only_newer -> not force
        if only_newer and not self.update_newer(last_revision):
            logging.info(
                u"[sync] No updates for %s after [revision: %d]",
                self.store.pootle_path, self.store.last_sync_revision)
            return

        if not self.store.file.exists():
            self.create_store_file(last_revision, user)
            return

        if conservative and self.store.is_template:
            return

        file_changed, changes = self.sync_store(
            last_revision,
            update_structure,
            conservative)
        self.save_store(
            last_revision,
            user,
            changes,
            (file_changed or not conservative))

    def sync_store(self, last_revision, update_structure, conservative):
        logging.info(u"Syncing %s", self.store.pootle_path)
        old_ids = set(self.disk_store.getids())
        new_ids = set(self.dbid_index.keys())
        file_changed = False
        changes = {}
        if update_structure:
            obsolete_units = self.get_units_to_obsolete(old_ids, new_ids)
            new_units = self.get_new_units(old_ids, new_ids)
            if obsolete_units or new_units:
                file_changed = True
                (changes['obsolete'],
                 changes['deleted'],
                 changes['added']) = self.update_structure(
                    obsolete_units,
                    new_units,
                    conservative=conservative)
        changes["updated"] = self.sync_units(
            self.get_common_units(
                set(self.dbid_index.get(uid)
                    for uid
                    in old_ids & new_ids),
                last_revision,
                conservative))
        return bool(file_changed or any(changes.values())), changes

    def save_store(self, last_revision, user, changes, updated):
        # TODO conservative -> not overwrite
        if updated:
            self.update_store_header(user=user)
            self.store.file.savestore()
            self.store.file_mtime = self.store.get_file_mtime()
            log(u"[sync] File saved; %s units in %s [revision: %d]" %
                (get_change_str(changes),
                 self.store.pootle_path,
                 last_revision))
        else:
            logging.info(
                u"[sync] nothing changed in %s [revision: %d]",
                self.store.pootle_path,
                last_revision)
        self.store.last_sync_revision = last_revision
        self.store.save()

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

    def sync_units(self, units):
        updated = 0
        for unit in units:
            match = self.disk_store.findid(unit.getid())
            if match is not None:
                changed = unit.sync(match)
                if changed:
                    updated += 1
        return updated

    def update_store_header(self, **kwargs_):
        self.disk_store.settargetlanguage(self.language.code)
        self.disk_store.setsourcelanguage(self.source_language.code)
