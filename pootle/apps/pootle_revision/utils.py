# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import uuid

from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property

from pootle.core.bulk import BulkCRUD
from pootle.core.signals import create, update
from pootle.core.url_helpers import split_pootle_path
from pootle_app.models import Directory
from pootle_translationproject.models import TranslationProject

from .models import Revision


class RevisionCRUD(BulkCRUD):
    model = Revision


class RevisionContext(object):

    def __init__(self, context):
        self.context = context

    @cached_property
    def content_type_id(self):
        return ContentType.objects.get_for_model(
            self.context._meta.model).id

    @property
    def revision_context(self):
        return self.context.revisions

    def get(self, key=None):
        """get a revision from db or set one if not set"""
        if not self.revision_context:
            return ""
        return self.revision_context.filter(
            key=key).values_list("value", flat=True).first() or ""

    def set(self, keys=None, value=None):
        """get a revision from db or set one if not set"""
        self.revision_context.filter(key__in=keys).delete()
        if value:
            revisions = []
            for k in keys:
                revisions.append(
                    Revision(
                        content_type_id=self.content_type_id,
                        object_id=self.context.pk,
                        key=k,
                        value=value))
            create.send(
                Revision,
                objects=revisions)


class DirectoryRevision(RevisionContext):
    pass


class LanguageRevision(RevisionContext):

    @property
    def revision_context(self):
        return self.context.directory.revisions


class ProjectRevision(RevisionContext):
    pass


class ProjectResourceRevision(RevisionContext):

    @property
    def revision_context(self):
        self.context.context.revisions


class ProjectSetRevision(RevisionContext):

    @property
    def revision_context(self):
        first_project = self.context.children.first()
        if not first_project:
            return
        return first_project.directory.parent.revisions


class TPRevision(RevisionContext):
    pass


class RevisionUpdater(object):

    def __init__(self, context=None, object_list=None, paths=None):
        self.context = context
        self.object_list = object_list
        self.paths = paths

    @property
    def object_list_paths(self):
        return set(
            self.object_list.values_list(
                self.related_pootle_path,
                flat=True))

    @property
    def all_pootle_paths(self):
        if self.context and not self.object_list:
            return set([self.context_path])
        elif self.object_list:
            parents = self.object_list_paths
            if self.context:
                parents.add(self.context_path)
            return parents
        elif self.paths:
            return self.paths
        return []

    @property
    def parents(self):
        """calculate unit parents for cache update"""
        return Directory.objects.filter(
            pootle_path__in=self.get_parent_paths(self.all_pootle_paths))

    def get_parent_paths(self, pootle_paths):
        if set(pootle_paths) == set(["/"]):
            return pootle_paths
        paths = set(["/projects/"])
        for pootle_path in pootle_paths:
            lang_code, proj_code, dir_path, __ = split_pootle_path(pootle_path)
            if proj_code:
                paths.add("/projects/%s/" % proj_code)
            if lang_code:
                paths.add("/%s/" % lang_code)
            if lang_code and proj_code:
                paths.add("/%s/%s/" % (lang_code, proj_code))
            dir_path_parts = dir_path.split("/")
            for i, name in enumerate(dir_path_parts):
                if not name:
                    continue
                paths.add(
                    "/%s/%s/%s/"
                    % (lang_code,
                       proj_code,
                       "/".join(dir_path_parts[:i + 1])))
        return paths

    @property
    def new_revision(self):
        return uuid.uuid4().hex

    @cached_property
    def content_type_id(self):
        return ContentType.objects.get_for_model(Directory).id

    def get_revisions(self, parents, keys=None):
        return Revision.objects.filter(
            content_type_id=self.content_type_id,
            key__in=keys or [""],
            object_id__in=parents)

    def update(self, keys=None):
        parents = list(self.parents.values_list("id", flat=True))
        revisions = self.get_revisions(parents, keys=keys)
        missing_revisions = []
        existing_ids = []
        revision_map = {
            '%s-%s' % (x['object_id'], x['key']): x['id']
            for x in revisions.values("id", "object_id", "key")}
        for parent in parents:
            for key in keys or [""]:
                id = '%s-%s' % (parent, key)
                if id in revision_map:
                    existing_ids.append(revision_map[id])
                else:
                    missing_revisions.append(dict(
                        object_id=parent,
                        key=key))
        new_revision = self.new_revision
        updates = {
            id: dict(value=new_revision)
            for id in existing_ids}
        if updates:
            update.send(
                Revision,
                updates=updates)
        if missing_revisions:
            create.send(
                Revision,
                objects=list(
                    self.create_missing_revisions(
                        missing_revisions, new_revision)))

    def create_missing_revisions(self, missing_revisions, new_revision):
        for revision in missing_revisions:
            yield Revision(
                content_type_id=self.content_type_id,
                object_id=revision['object_id'],
                key=revision['key'],
                value=new_revision)


class UnitRevisionUpdater(RevisionUpdater):
    related_pootle_path = "store__parent__pootle_path"

    @property
    def context_path(self):
        return self.context.store.parent.pootle_path


class StoreRevisionUpdater(RevisionUpdater):
    related_pootle_path = "parent__pootle_path"

    @property
    def context_path(self):
        return self.context.parent.pootle_path


class DirectoryRevisionUpdater(RevisionUpdater):
    related_pootle_path = "pootle_path"

    @property
    def context_path(self):
        return self.context.pootle_path


class ProjectRevisionUpdater(RevisionUpdater):
    related_pootle_path = "pootle_path"

    @property
    def context_path(self):
        return self.context.pootle_path

    def get_parent_paths(self, pootle_paths):
        paths = set(["/projects/"])
        projects = set()
        for pootle_path in pootle_paths:
            lang_code, proj_code, dir_path, __ = split_pootle_path(pootle_path)
            paths.add("/projects/%s/" % proj_code)
            projects.add(proj_code)
        tps = TranslationProject.objects.filter(
            project__code__in=projects).values_list("language__code", flat=True)
        for lang_code in tps.iterator():
            paths.add("/%s/" % lang_code)
        return paths
