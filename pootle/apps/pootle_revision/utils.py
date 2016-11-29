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

from pootle.core.url_helpers import split_pootle_path
from pootle_app.models import Directory

from .models import Revision


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
            Revision.objects.bulk_create(revisions)


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
        first_child = self.context.children.first()
        if not first_child:
            return
        return Directory.objects.get(
            pootle_path="/projects/%s/"
            % split_pootle_path(first_child.pootle_path)[1]).revisions


class ProjectSetRevision(RevisionContext):

    @property
    def revision_context(self):
        first_project = self.context.children.first()
        if not first_project:
            return
        return first_project.directory.parent.revisions


class TPRevision(RevisionContext):

    @property
    def revision_context(self):
        return self.context.directory.revisions


class RevisionUpdater(object):

    def __init__(self, context=None, object_list=None):
        self.context = context
        self.object_list = object_list

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
        return []

    @property
    def parents(self):
        """calculate unit parents for cache update"""
        return Directory.objects.filter(
            pootle_path__in=self.get_parent_paths(self.all_pootle_paths))

    def get_parent_paths(self, pootle_paths):
        paths = set(["/projects/"])
        for pootle_path in pootle_paths:
            lang_code, proj_code, dir_path, __ = split_pootle_path(pootle_path)
            paths.add("/projects/%s/" % proj_code)
            paths.add("/%s/" % lang_code)
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

    def create_revisions(self, parents, keys=None):
        new_revision = self.new_revision
        for parent in parents:
            for key in keys or [""]:
                yield Revision(
                    content_type_id=self.content_type_id,
                    object_id=parent,
                    key=key,
                    value=new_revision)

    def update(self, keys=None):
        parents = list(self.parents.values_list("id", flat=True))
        revisions = self.get_revisions(parents, keys=keys)
        revisions._raw_delete(revisions.db)
        Revision.objects.bulk_create(
            self.create_revisions(parents, keys=keys))


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
