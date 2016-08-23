# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model

from pootle.core.delegate import format_updaters
from pootle.core.models import Revision
from pootle_statistics.models import SubmissionTypes
from pootle_store.constants import OBSOLETE, SOURCE_WINS
from pootle_store.store.deserialize import StoreDeserialization
from pootle_store.diff import StoreDiff
from pootle_store.store.serialize import StoreSerialization


User = get_user_model()


class TPTool(object):

    def __init__(self, project):
        self.project = project

    def __getitem__(self, language_code):
        """Access to Project TPs by language_code"""
        return self.tp_qs.get(language__code=language_code)

    @property
    def tp_qs(self):
        """Queryset of translation_projects"""
        return self.project.translationproject_set

    def check_no_tp(self, language):
        """Check a TP doesn't exist already for a given language.
        """
        if self.get_tp(language):
            raise ValueError(
                "TranslationProject '%s' already exists"
                % self.get_path(language.code))

    def check_tp(self, tp):
        """Check if a TP is part of our Project"""
        if tp.project != self.project:
            raise ValueError(
                "TP '%s' is not part of project '%s'"
                % (tp, self.project.code))

    def clone(self, tp, language, update_cache=True):
        """Clone a TP to a given language. Raises Exception if an existing TP
        exists for that Language.
        """
        self.check_tp(tp)
        self.check_no_tp(language)
        new_tp = self.create_tp(language)
        self.clone_children(
            tp.directory,
            new_tp.directory,
            update_cache=update_cache)
        return new_tp

    def clone_children(self, source_dir, target_parent, update_cache=True):
        """Clone a source Directory's children to a given target Directory.
        """
        for store in source_dir.child_stores.filter(obsolete=False):
            self.clone_store(store, target_parent, update_cache=update_cache)
        for subdir in source_dir.child_dirs.filter(obsolete=False):
            self.clone_directory(subdir, target_parent, update_cache=update_cache)

    def clone_directory(self, source_dir, target_parent, update_cache=True):
        """Clone a source Directory and its children to a given target
        Directory. Raises Exception if the target exists already.
        """
        target_dir = target_parent.child_dirs.create(
            name=source_dir.name)
        self.clone_children(
            source_dir,
            target_dir,
            update_cache=update_cache)
        return target_dir

    def clone_store(self, store, target_dir, update_cache=True):
        """Clone given Store to target Directory"""
        cloned = target_dir.child_stores.create(
            name=store.name, translation_project=store.translation_project)
        if update_cache:
            cloned.mark_all_dirty()
        cloned.filetype = store.filetype
        self.store_updater(cloned).update(
            self.store_deserializer(cloned).deserialize(
                self.store_serializer(store).serialize()))
        cloned.state = store.state
        cloned.save()
        return cloned

    def create_tp(self, language):
        """Create a TP for a given language"""
        tp_dir = language.directory.child_dirs.create(
            name=self.project.code)
        return self.tp_qs.create(
            language=language, directory=tp_dir)

    def get(self, language_code, default=None):
        """Given a language code, returns the relevant TP.
        If the TP doesn't exist returns a `default` or `None`.
        """
        try:
            return self[language_code]
        except self.tp_qs.model.DoesNotExist:
            return default

    def get_path(self, language_code):
        """Returns the pootle_path of a TP for a given language_code"""
        return "/%s/%s/" % (language_code, self.project.code)

    def get_tp(self, language):
        """Given a language return the related TP"""
        try:
            return self.tp_qs.get(language=language)
        except self.tp_qs.model.DoesNotExist:
            pass

    def move(self, tp, language, update_cache=True):
        """Re-assign a tp to a different language"""
        self.check_tp(tp)
        if tp.language == language:
            return
        self.check_no_tp(language)
        pootle_path = self.get_path(language.code)
        directory = tp.directory
        tp.language = language
        tp.pootle_path = pootle_path
        directory.pootle_path = pootle_path
        directory.parent = language.directory
        directory.save()
        tp.save()
        self.set_parents(
            directory, directory,
            update_cache=update_cache)

    def set_parents(self, directory, parent, update_cache=True):
        """Recursively sets the parent for children of a directory"""
        for store in directory.child_stores.all():
            if update_cache:
                store.clear_all_cache(parents=False, children=False)
            store.parent = parent
            store.pootle_path = "%s%s/" % (parent.pootle_path, store.name)
            if update_cache:
                store.mark_all_dirty()
            store.save()
        for subdir in directory.child_dirs.all():
            if update_cache:
                subdir.clear_all_cache(parents=False, children=False)
            subdir.parent = parent
            subdir.pootle_path = "%s%s/" % (parent.pootle_path, subdir.name)
            subdir.save()
            self.set_parents(subdir, subdir, update_cache=update_cache)

    def store_deserializer(self, store):
        return StoreDeserialization(store)

    def store_serializer(self, store):
        return StoreSerialization(store)

    def store_updater(self, store):
        updaters = format_updaters.gather()
        updater_class = (
            updaters.get(store.filetype.name)
            or updaters.get("default"))
        return updater_class(store)

    def update_children(self, source_dir, target_dir, update_cache=True):
        """Update a target Directory and its children from a given
        source Directory
        """
        stores = []
        dirs = []
        for store in source_dir.child_stores.filter(obsolete=False):
            stores.append(store.name)
            try:
                self.update_store(
                    store,
                    target_dir.child_stores.get(name=store.name))
            except target_dir.child_stores.model.DoesNotExist:
                self.clone_store(store, target_dir, update_cache=update_cache)
        for subdir in source_dir.child_dirs.filter(obsolete=False):
            dirs.append(subdir.name)
            try:
                self.update_children(
                    subdir,
                    target_dir.child_dirs.get(name=subdir.name),
                    update_cache=update_cache)
            except target_dir.child_dirs.model.DoesNotExist:
                self.clone_directory(
                    subdir, target_dir, update_cache=update_cache)

        for store in target_dir.child_stores.exclude(name__in=stores):
            store.makeobsolete()

    def update_from_tp(self, source, target, update_cache=True):
        """Update one TP from another"""
        self.check_tp(source)
        self.check_tp(target)
        self.update_children(
            source.directory, target.directory, update_cache=update_cache)

    def update_store(self, source, target):
        """Update a target Store from a given source Store"""
        source_revision = target.get_max_unit_revision() + 1
        differ = StoreDiff(target, source, source_revision)
        diff = differ.diff()
        if diff is None:
            return
        system = User.objects.get_system_user()
        update_revision = Revision.incr()
        return target.update_from_diff(
            source,
            source_revision,
            diff,
            update_revision,
            system,
            SubmissionTypes.SYSTEM,
            SOURCE_WINS,
            True)
