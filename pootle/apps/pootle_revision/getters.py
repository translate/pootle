# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import crud, revision, revision_updater
from pootle.core.plugin import getter
from pootle_app.models import Directory
from pootle_language.models import Language
from pootle_project.models import Project, ProjectResource, ProjectSet
from pootle_store.models import Store, Unit
from pootle_translationproject.models import TranslationProject

from .models import Revision
from .utils import (
    DirectoryRevision, DirectoryRevisionUpdater, LanguageRevision,
    ProjectResourceRevision, ProjectRevision, ProjectRevisionUpdater,
    ProjectSetRevision, RevisionCRUD, StoreRevisionUpdater, TPRevision,
    UnitRevisionUpdater)


CRUD = {
    Revision: RevisionCRUD()}


@getter(crud, sender=(Revision, ))
def data_crud_getter(**kwargs):
    return CRUD[kwargs["sender"]]


@getter(revision, sender=Directory)
def directory_revision_getter(**kwargs):
    return DirectoryRevision


@getter(revision, sender=Language)
def language_revision_getter(**kwargs):
    return LanguageRevision


@getter(revision, sender=Project)
def project_revision_getter(**kwargs):
    return ProjectRevision


@getter(revision, sender=ProjectResource)
def project_resource_revision_getter(**kwargs):
    return ProjectResourceRevision


@getter(revision, sender=ProjectSet)
def project_set_revision_getter(**kwargs):
    return ProjectSetRevision


@getter(revision, sender=TranslationProject)
def tp_revision_getter(**kwargs):
    return TPRevision


@getter(revision_updater, sender=Directory)
def directory_revision_updater_getter(**kwargs):
    return DirectoryRevisionUpdater


@getter(revision_updater, sender=Unit)
def units_revision_updater_getter(**kwargs):
    return UnitRevisionUpdater


@getter(revision_updater, sender=Store)
def stores_revision_updater_getter(**kwargs):
    return StoreRevisionUpdater


@getter(revision_updater, sender=Project)
def project_revision_updater_getter(**kwargs):
    return ProjectRevisionUpdater
