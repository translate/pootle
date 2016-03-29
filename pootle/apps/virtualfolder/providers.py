# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import (
    context_data,
    object_stats, object_parents, pootle_paths,
    object_resources, search_filters)
from pootle.core.plugin import provider
from pootle.core.url_helpers import get_all_pootle_paths
from pootle_app.models import Directory
from pootle_language.views import LanguageTranslateView
from pootle_project.models import Project
from pootle_project.views import ProjectsTranslateView, ProjectTranslateView
from pootle_store.models import Store
from pootle_store.unit.search import DBSearchBackend
from pootle_store.views import UnitEditJSON
from pootle_translationproject.views import (
    TPBrowseView, TPTranslateStoreView, TPTranslateView)

from .context import (
    VFolderLanguageTranslateContext,
    VFolderProjectTranslateContext,
    VFolderProjectsTranslateContext,
    VFolderTPBrowseContext,
    VFolderTPTranslateContext,
    VFolderTPTranslateStoreContext)
from .models import VirtualFolderTreeItem


@provider(context_data, sender=TPTranslateStoreView)
def get_vfolder_tp_translate_store_context_data(sender, **kwargs):
    return VFolderTPTranslateStoreContext(
        view=kwargs["view"], context=kwargs["context"]).get_context_data()


@provider(context_data, sender=TPTranslateView)
def get_vfolder_tp_translate_context_data(sender, **kwargs):
    return VFolderTPTranslateContext(
        view=kwargs["view"], context=kwargs["context"]).get_context_data()


@provider(context_data, sender=TPBrowseView)
def get_vfolder_tp_browse_context_data(sender, **kwargs):
    return VFolderTPBrowseContext(
        view=kwargs["view"], context=kwargs["context"]).get_context_data()


@provider(context_data, sender=UnitEditJSON)
def get_vfolder_unit_edit_context_data(sender, **kwargs):
    return dict(priority=kwargs['view'].object.priority)


@provider(context_data, sender=ProjectTranslateView)
def get_vfolder_project_translate_context_data(sender, **kwargs):
    return VFolderProjectTranslateContext(
        view=kwargs["view"], context=kwargs["context"]).get_context_data()


@provider(context_data, sender=ProjectsTranslateView)
def get_vfolder_projects_translate_context_data(sender, **kwargs):
    return VFolderProjectsTranslateContext(
        view=kwargs["view"], context=kwargs["context"]).get_context_data()


@provider(context_data, sender=LanguageTranslateView)
def get_vfolder_language_translate_context_data(sender, **kwargs):
    return VFolderLanguageTranslateContext(
        view=kwargs["view"], context=kwargs["context"]).get_context_data()


@provider(object_parents, sender=Store)
def gather_vfolder_parents(sender, **kwargs):
    return kwargs["instance"].parent_vf_treeitems.all()


@provider(pootle_paths, sender=Store)
def gather_vfolder_pootle_paths(sender, **kwargs):
    vftis = kwargs["instance"].parent_vf_treeitems.values_list(
        "vfolder__location", "pootle_path")
    pootle_paths = []
    for location, pootle_path in vftis:
        pootle_paths.extend(
            [p for p
             in get_all_pootle_paths(pootle_path)
             if p.count('/') > location.count('/')])
    return pootle_paths


@provider(object_stats, sender=Directory)
def get_vfolder_object_stats(sender, **kwargs):
    stats = dict(vfolders={})
    for vfolder_treeitem in kwargs["instance"].vf_treeitems.iterator():
        if kwargs['user'].is_superuser or vfolder_treeitem.is_visible:
            stats['vfolders'][vfolder_treeitem.code] = (
                vfolder_treeitem.get_stats(include_children=False))
    return stats


@provider(object_resources, sender=Project)
def gather_vfolder_resources(sender, **kwargs):
    return (
        VirtualFolderTreeItem.objects.filter(
            vfolder__is_public=True,
            pootle_path__regex=r"^/[^/]*/%s/" % kwargs["instance"].code))


@provider(search_filters, sender=DBSearchBackend)
def gather_vfolder_search_filters(sender, **kwargs):
    filter_kwargs = kwargs["filter_kwargs"]
    filter_vfolder = (
        filter_kwargs.get("path_extra")
        and filter_kwargs["path_extra"].get("vfolder"))
    if filter_vfolder:
        return dict(vfolders=filter_kwargs["path_extra"]["vfolder"])
