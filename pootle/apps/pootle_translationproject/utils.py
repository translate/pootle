# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model

from pootle.core.contextmanagers import keep_data
from pootle.core.models import Revision
from pootle.core.paths import Paths
from pootle.core.signals import create, update_checks
from pootle_statistics.models import SubmissionTypes
from pootle_store.constants import OBSOLETE, SOURCE_WINS
from pootle_store.diff import StoreDiff
from pootle_store.models import QualityCheck

from .apps import PootleTPConfig
from .contextmanagers import update_tp_after


User = get_user_model()


class TPPaths(Paths):
    ns = "pootle.tp"
    sw_version = PootleTPConfig.version

    @property
    def store_qs(self):
        return self.context.stores.all()


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
        with update_tp_after(new_tp):
            self.clone_children(
                tp.directory,
                new_tp.directory)
        return new_tp

    def clone_children(self, source_dir, target_parent):
        """Clone a source Directory's children to a given target Directory.
        """
        source_stores = source_dir.child_stores.live().select_related(
            "data", "filetype", "filetype__extension")
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
        with keep_data(signals=(update_checks, )):
            cloned.update(cloned.deserialize(store.serialize()))
            cloned.state = store.state
            cloned.filetype = store.filetype
            cloned.save()
        self.clone_checks(store, cloned)
        return cloned

    def clone_checks(self, source_store, target_store):
        """Clone checks from source store to target store."""
        fields = ('unit__unitid_hash', 'category', 'name',
                  'false_positive', 'message')
        checks = QualityCheck.objects.filter(
            unit__store=source_store,
            unit__state__gt=OBSOLETE,
        ).values(*fields)
        unitid_hashes = [x['unit__unitid_hash'] for x in checks]
        units = target_store.units.filter(unitid_hash__in=unitid_hashes)
        unit_map = {
            x['unitid_hash']: x['id']
            for x in units.values('id', 'unitid_hash')}

        cloned_checks = []
        for check in checks:
            cloned_checks.append(QualityCheck(
                unit_id=unit_map[check['unit__unitid_hash']],
                category=check['category'],
                name=check['name'],
                false_positive=check['false_positive'],
                message=check['message']))
        create.send(QualityCheck, objects=cloned_checks)

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
            return tp_qs.select_related(
                "directory",
                "directory__parent").get(language=language)
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
        with update_tp_after(tp):
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

    def update_children(self, source_dir, target_dir):
        """Update a target Directory and its children from a given
        source Directory
        """
        stores = []
        dirs = []
        source_stores = source_dir.child_stores.select_related(
            "filetype__extension",
            "filetype__template_extension")
        for store in source_stores:
            store.parent = source_dir
            stores.append(store.name)
            try:
                self.update_store(
                    store,
                    target_dir.child_stores.select_related(
                        "filetype__extension",
                        "filetype__template_extension").get(name=store.name))
            except target_dir.child_stores.model.DoesNotExist:
                self.clone_store(store, target_dir)
        for subdir in source_dir.child_dirs.live():
            subdir.parent = source_dir
            dirs.append(subdir.name)
            try:
                self.update_children(
                    subdir,
                    target_dir.child_dirs.get(name=subdir.name))
            except target_dir.child_dirs.model.DoesNotExist:
                self.clone_directory(subdir, target_dir)

        for store in target_dir.child_stores.exclude(name__in=stores):
            store.makeobsolete()

    def update_from_tp(self, source, target):
        """Update one TP from another"""
        self.check_tp(source)
        self.check_tp(target)

        with update_tp_after(target):
            self.update_children(
                source.directory, target.directory)

    def update_store(self, source, target):
        """Update a target Store from a given source Store"""
        source_revision = target.data.max_unit_revision + 1
        differ = StoreDiff(target, source, source_revision)
        diff = differ.diff()
        if diff is None:
            return
        system = User.objects.get_system_user()
        update_revision = Revision.incr()
        return target.updater.update_from_diff(
            source,
            source_revision,
            diff,
            update_revision,
            system,
            SubmissionTypes.SYSTEM,
            SOURCE_WINS,
            True)
