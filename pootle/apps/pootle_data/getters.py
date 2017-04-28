# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import crud, data_tool, data_updater
from pootle.core.plugin import getter
from pootle_app.models import Directory
from pootle_language.models import Language
from pootle_project.models import Project, ProjectResource, ProjectSet
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject

from .directory_data import DirectoryDataTool
from .language_data import LanguageDataTool
from .models import StoreChecksData, StoreData, TPChecksData, TPData
from .project_data import (
    ProjectDataTool, ProjectResourceDataTool, ProjectSetDataTool)
from .store_data import (
    StoreChecksDataCRUD, StoreDataCRUD, StoreDataTool, StoreDataUpdater)
from .tp_data import (
    TPChecksDataCRUD, TPDataCRUD, TPDataTool, TPDataUpdater, TPUpdater)


CRUD = {
    StoreData: StoreDataCRUD(),
    StoreChecksData: StoreChecksDataCRUD(),
    TPData: TPDataCRUD(),
    TPChecksData: TPChecksDataCRUD()}


@getter(crud, sender=(StoreChecksData, StoreData, TPChecksData, TPData))
def data_crud_getter(**kwargs):
    return CRUD[kwargs["sender"]]


@getter(data_tool, sender=Store)
def store_data_tool_getter(**kwargs_):
    return StoreDataTool


@getter(data_updater, sender=TranslationProject)
def store_updater_getter(**kwargs_):
    return TPUpdater


@getter(data_updater, sender=StoreDataTool)
def store_data_tool_updater_getter(**kwargs_):
    return StoreDataUpdater


@getter(data_tool, sender=TranslationProject)
def tp_data_tool_getter(**kwargs_):
    return TPDataTool


@getter(data_updater, sender=TPDataTool)
def tp_data_tool_updater_getter(**kwargs_):
    return TPDataUpdater


@getter(data_tool, sender=Project)
def project_data_tool_getter(**kwargs_):
    return ProjectDataTool


@getter(data_tool, sender=ProjectSet)
def project_set_data_tool_getter(**kwargs_):
    return ProjectSetDataTool


@getter(data_tool, sender=ProjectResource)
def project_resource_data_tool_getter(**kwargs_):
    return ProjectResourceDataTool


@getter(data_tool, sender=Language)
def language_data_tool_getter(**kwargs_):
    return LanguageDataTool


@getter(data_tool, sender=Directory)
def directory_data_tool_getter(**kwargs_):
    return DirectoryDataTool
