# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model

from pootle.core.models import Revision
from pootle_statistics.models import SubmissionTypes
from pootle_store.constants import SOURCE_WINS
from pootle_store.diff import StoreDiff


User = get_user_model()


class TPTool(object):

    def __init__(self, project):
        self.project = project

    @property
    def tp_qs(self):
        return self.project.translationproject_set

    def get_path(self, language_code):
        return "/%s/%s/" % (language_code, self.project.code)

    def get_tp(self, language):
        try:
            return self.tp_qs.get(language=language)
        except self.tp_qs.model.DoesNotExist:
            pass

    def check_tp(self, tp):
        if tp.project != self.project:
            raise ValueError(
                "TP '%s' is not part of project '%s'"
                % (tp, self.project.code))

    def create_tp(self, language):
        return self.tp_qs.create(language=language)

    def update_from_tp(self, source, target):
        self.check_tp(source)
        self.check_tp(target)
        self.update_children(source.directory, target.directory)

    def update_store(self, source, target):
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

    def update_children(self, source_dir, target_dir):
        stores = []
        dirs = []
        for store in source_dir.child_stores.live():
            stores.append(store.name)
            try:
                self.update_store(
                    store,
                    target_dir.child_stores.get(name=store.name))
            except target_dir.child_stores.model.DoesNotExist:
                self.clone_store(store, target_dir)
        for subdir in source_dir.child_dirs.live():
            dirs.append(subdir.name)
            try:
                self.update_children(
                    subdir,
                    target_dir.child_dirs.get(name=subdir.name))
            except target_dir.child_dirs.model.DoesNotExist:
                self.clone_directory(subdir, target_dir)

        for store in target_dir.child_stores.exclude(name__in=stores):
            store.makeobsolete()

    def clone_store(self, store, target_dir):
        cloned = target_dir.child_stores.create(
            name=store.name,
            translation_project=target_dir.translation_project)
        cloned.mark_all_dirty()
        cloned.update(cloned.deserialize(store.serialize()))
        cloned.state = store.state
        cloned.save()
        return cloned

    def clone(self, tp, language):
        self.check_tp(tp)
        self.check_no_tp(language)
        new_tp = self.create_tp(language)
        self.clone_children(
            tp.directory,
            new_tp.directory)
        return new_tp

    def clone_directory(self, source_dir, target_parent):
        target_dir = target_parent.child_dirs.create(
            name=source_dir.name)
        self.clone_children(
            source_dir,
            target_dir)
        return target_dir

    def clone_children(self, source_dir, target_parent):
        for store in source_dir.child_stores.live():
            self.clone_store(store, target_parent)
        for subdir in source_dir.child_dirs.live():
            self.clone_directory(subdir, target_parent)

    def check_no_tp(self, language):
        if self.get_tp(language):
            raise ValueError(
                "TranslationProject '%s' already exists"
                % self.get_path(language.code))

    def set_parents(self, directory, parent):
        """Recursively sets the parent for children of a directory"""
        self.check_tp(directory.translation_project)
        self.check_tp(parent.translation_project)
        for store in directory.child_stores.all():
            store.clear_all_cache(parents=False, children=False)
            store.parent = parent
            store.mark_all_dirty()
            store.save()
        for subdir in directory.child_dirs.all():
            subdir.clear_all_cache(parents=False, children=False)
            subdir.parent = parent
            subdir.save()
            self.set_parents(subdir, subdir)

    def move(self, tp, language):
        """Re-assign a tp to a different language"""
        self.check_tp(tp)
        if tp.language == language:
            return
        self.check_no_tp(language)
        pootle_path = self.get_path(language.code)
        directory = tp.directory
        tp.language = language
        tp.pootle_path = pootle_path
        tp.save()
        self.set_parents(directory, self.get_tp(language).directory)
        directory.delete()
