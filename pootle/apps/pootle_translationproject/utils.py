# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import shutil

from django.contrib.auth import get_user_model

from pootle.core.models import Revision
from pootle.core.signals import update_data
from pootle_statistics.models import SubmissionTypes
from pootle_store.constants import SOURCE_WINS
from pootle_store.diff import StoreDiff
from pootle_store.models import QualityCheck


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
        return self.get_tps(self.project)

    def get_tps(self, project):
        return project.translationproject_set

    def check_no_tp(self, language, project=None):
        """Check a TP doesn't exist already for a given language.
        """
        if self.get_tp(language, project):
            raise ValueError(
                "TranslationProject '%s' already exists"
                % self.get_path(
                    language.code,
                    project and project.code or None))

    def check_tp(self, tp):
        """Check if a TP is part of our Project"""
        if tp.project != self.project:
            raise ValueError(
                "TP '%s' is not part of project '%s'"
                % (tp, self.project.code))

    def clone(self, tp, language, project=None):
        """Clone a TP to a given language. Raises Exception if an existing TP
        exists for that Language.
        """
        if not project:
            self.check_tp(tp)
        self.check_no_tp(language, project)
        new_tp = self.create_tp(language, project)
        new_tp.directory.tp = new_tp
        new_tp.directory.translationproject = new_tp
        self.clone_children(
            tp.directory,
            new_tp.directory)
        if self.project.treestyle != 'pootle_fs':
            self.clone_disk_directory_content(tp, new_tp)
        return new_tp

    def clone_disk_directory_content(self, source, target):
        if not os.path.exists(source.abs_real_path):
            return

        for item in os.listdir(source.abs_real_path):
            source_path = os.path.join(source.abs_real_path, item)
            target_path = os.path.join(target.abs_real_path, item)
            if os.path.isdir(source_path):
                shutil.copytree(source_path, target_path)
            else:
                shutil.copy(source_path, target_path)

    def clone_children(self, source_dir, target_parent):
        """Clone a source Directory's children to a given target Directory.
        """
        source_stores = source_dir.child_stores.live().select_related(
            "filetype", "filetype__extension")
        for store in source_stores:
            store.parent = source_dir
            self.clone_store(store, target_parent)
        for subdir in source_dir.child_dirs.live():
            subdir.parent = source_dir
            self.clone_directory(subdir, target_parent)

    def clone_directory(self, source_dir, target_parent):
        """Clone a source Directory and its children to a given target
        Directory. Raises Exception if the target exists already.
        """
        target_dir = target_parent.child_dirs.create(
            name=source_dir.name, tp=target_parent.translation_project)
        target_dir.parent = target_parent
        self.clone_children(
            source_dir,
            target_dir)
        return target_dir

    def clone_store(self, store, target_dir):
        """Clone given Store to target Directory"""
        cloned = target_dir.child_stores.create(
            name=store.name,
            translation_project=target_dir.translation_project)
        cloned.update(cloned.deserialize(store.serialize()))
        cloned.state = store.state
        cloned.filetype = store.filetype
        cloned.save()
        self.update_muted_checks(store, cloned)
        return cloned

    def update_muted_checks(self, source_store, target_store,
                            check_target_translation=False):
        """Mute false positive checks in target store."""
        fields = ('unit__unitid_hash', 'category', 'name')
        if check_target_translation:
            fields += ('unit__target_f',)
        false_positive_checks = QualityCheck.objects.filter(
            unit__store=source_store,
            false_positive=True
        ).values(*fields)

        qs = QualityCheck.objects.none()
        for check in false_positive_checks:
            params = dict(
                unit__store=target_store,
                unit__unitid_hash=check['unit__unitid_hash'],
                category=check['category'],
                name=check['name'],
            )
            if check_target_translation:
                params['unit__target_f'] = check['unit__target_f']
            qs = qs | QualityCheck.objects.filter(**params)

        qs.update(false_positive=True)
        update_data.send(
            target_store.__class__, instance=target_store)

    def create_tp(self, language, project=None):
        """Create a TP for a given language"""
        tp_qs = (
            self.get_tps(project)
            if project
            else self.tp_qs)
        return tp_qs.create(language=language)

    def get(self, language_code, default=None):
        """Given a language code, returns the relevant TP.
        If the TP doesn't exist returns a `default` or `None`.
        """
        try:
            return self[language_code]
        except self.tp_qs.model.DoesNotExist:
            return default

    def get_path(self, language_code, project_code=None):
        """Returns the pootle_path of a TP for a given language_code"""
        return (
            "/%s/%s/"
            % (language_code,
               (project_code
                and project_code
                or self.project.code)))

    def get_tp(self, language, project=None):
        """Given a language return the related TP"""
        tp_qs = (
            self.get_tps(project)
            if project
            else self.tp_qs)
        try:
            return tp_qs.get(language=language)
        except tp_qs.model.DoesNotExist:
            pass

    def move(self, tp, language, project=None):
        """Re-assign a tp to a different language"""
        if not project:
            self.check_tp(tp)
        if not project and (tp.language == language):
            return
        self.check_no_tp(language, project)
        pootle_path = self.get_path(
            language.code,
            project and project.code or None)
        directory = tp.directory
        if project:
            tp.project = project
        tp.language = language
        tp.pootle_path = pootle_path
        tp.save()
        self.set_parents(
            directory,
            self.get_tp(language, project).directory,
            project=project)
        directory.delete()

    def set_parents(self, directory, parent, project=None):
        """Recursively sets the parent for children of a directory"""
        if not project:
            self.check_tp(directory.translation_project)
            self.check_tp(parent.translation_project)
        for store in directory.child_stores.all():
            store.parent = parent
            store.save()
        for subdir in directory.child_dirs.all():
            subdir.parent = parent
            subdir.save()
            self.set_parents(subdir, subdir, project)

    def update_children(self, source_dir, target_dir,
                        allow_add_and_obsolete=True,
                        resolve_conflict=SOURCE_WINS):
        """Update a target Directory and its children from a given
        source Directory
        """
        stores = []
        dirs = []
        source_stores = source_dir.child_stores.select_related(
            "translation_project")
        for store in source_stores:
            store.parent = source_dir
            stores.append(store.name)
            try:
                self.update_store(
                    store,
                    target_dir.child_stores.get(name=store.name),
                    allow_add_and_obsolete=allow_add_and_obsolete,
                    resolve_conflict=resolve_conflict
                )
            except target_dir.child_stores.model.DoesNotExist:
                if allow_add_and_obsolete:
                    self.clone_store(store, target_dir)
        for subdir in source_dir.child_dirs.live():
            subdir.parent = source_dir
            dirs.append(subdir.name)
            try:
                self.update_children(
                    subdir,
                    target_dir.child_dirs.get(name=subdir.name),
                    allow_add_and_obsolete=allow_add_and_obsolete,
                )
            except target_dir.child_dirs.model.DoesNotExist:
                self.clone_directory(subdir, target_dir)

        if allow_add_and_obsolete:
            for store in target_dir.child_stores.exclude(name__in=stores):
                store.makeobsolete()

    def update_from_tp(self, source, target, allow_add_and_obsolete=True,
                       resolve_conflict=SOURCE_WINS):
        """Update one TP from another"""
        self.check_tp(source)
        self.update_children(
            source.directory, target.directory,
            allow_add_and_obsolete=allow_add_and_obsolete,
            resolve_conflict=resolve_conflict
        )

    def update_store(self, source, target, allow_add_and_obsolete=True,
                     resolve_conflict=SOURCE_WINS):
        """Update a target Store from a given source Store"""
        source_revision = target.data.max_unit_revision + 1
        differ = StoreDiff(target, source, source_revision)
        diff = differ.diff()
        if diff is not None:
            system = User.objects.get_system_user()
            update_revision = Revision.incr()
            target.updater.update_from_diff(
                source,
                source_revision,
                diff,
                update_revision,
                system,
                SubmissionTypes.SYSTEM,
                resolve_conflict,
                allow_add_and_obsolete)
        self.update_muted_checks(source, target, check_target_translation=True)
