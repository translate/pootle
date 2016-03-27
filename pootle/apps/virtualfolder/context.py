# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.utils.functional import cached_property

from pootle.core.browser import get_table_headings
from pootle.core.utils.json import jsonify

from .helpers import make_vfolder_treeitem_dict, vftis_for_child_dirs


class ViewContext(object):

    def __init__(self, view, context):
        self.view = view
        self.context = context


class VFolderTPBrowseContext(ViewContext):

    @property
    def vftis(self):
        vftis = self.view.object.vf_treeitems
        if not self.view.is_admin:
            vftis = vftis.filter(vfolder__is_public=True)
        return vftis

    @cached_property
    def vfolders(self):
        return [
            make_vfolder_treeitem_dict(vfolder_treeitem)
            for vfolder_treeitem
            in self.vftis.order_by('-vfolder__priority').select_related("vfolder")
            if (self.view.is_admin
                or vfolder_treeitem.is_visible)]

    @property
    def vfolder_stats(self):
        stats = {"vfolders": {}}
        for vfolder_treeitem in self.vfolders or []:
            stats['vfolders'][
                vfolder_treeitem['code']] = vfolder_treeitem["stats"]
            del vfolder_treeitem["stats"]
        return stats

    def get_context_data(self):
        ctx = {}
        if len(self.vfolders) > 0:
            table_fields = [
                'name', 'priority', 'progress', 'total',
                'need-translation', 'suggestions', 'critical',
                'last-updated', 'activity']
            ctx.update(
                {'vfolders': {'id': 'vfolders',
                              'fields': table_fields,
                              'headings': get_table_headings(table_fields),
                              'items': self.vfolders}})
        ctx["stats"] = jsonify(self.stats)
        if self.context.get("table"):
            ctx["table"] = self.table

        if self.has_vfolders and (self.view.language or self.view.is_admin):
            filters = dict(sort="priority")
            ctx['url_action_continue'] = self.view.object.get_translate_url(
                state='incomplete', **filters)
            ctx['url_action_fixcritical'] = self.view.object.get_critical_url(
                **filters)
            ctx['url_action_review'] = self.view.object.get_translate_url(
                state='suggestions', **filters)
        return ctx

    @cached_property
    def has_vfolders(self):
        return self.view.object.vf_treeitems.count() > 0

    @property
    def table(self):
        dirs_with_vfolders = set(
            vftis_for_child_dirs(self.view.object).values_list(
                "directory__pk", flat=True))
        kwargs = dict(sort="priority")
        for i, item in enumerate(self.context["table"]["items"]):
            if item["pk"] in dirs_with_vfolders:
                ob = self.view.get_child(item["pk"])
                href_todo = ob.get_translate_url(
                    state='incomplete', **kwargs)
                href_sugg = ob.get_translate_url(
                    state='suggestions', **kwargs)
                href_critical = ob.get_critical_url(**kwargs)
                self.context["table"]["items"][i].update(
                    {'href_todo': href_todo,
                     'href_sugg': href_sugg,
                     'href_critical': href_critical})
        return self.context["table"]

    @property
    def stats(self):
        stats = self.vfolder_stats
        if stats and stats["vfolders"]:
            stats.update(self.view.stats)
        else:
            stats = self.view.stats
        return stats


class VFolderTranslateContext(ViewContext):

    @property
    def vfolder(self):
        return self.view.extracted_path[2].get("vfolder")

    @property
    def vfolder_pk(self):
        return self.vfolder and self.vfolder.pk or ""

    @cached_property
    def has_vfolders(self):
        return self.view.object.vf_treeitems.count() > 0

    @property
    def display_vfolder_priority(self):
        if self.vfolder:
            return False
        return self.has_vfolders

    def get_context_data(self):
        return {
            'display_priority': self.display_vfolder_priority,
            'current_vfolder_pk': self.vfolder_pk}


class VFolderTPTranslateContext(VFolderTranslateContext):
    pass


class VFolderTPTranslateStoreContext(VFolderTPTranslateContext):

    @property
    def display_vfolder_priority(self):
        return False


class VFolderProjectTranslateContext(VFolderTranslateContext):

    @property
    def display_vfolder_priority(self):
        return False


class VFolderProjectsTranslateContext(VFolderTranslateContext):

    @property
    def display_vfolder_priority(self):
        return False


class VFolderLanguageTranslateContext(VFolderTranslateContext):

    @property
    def display_vfolder_priority(self):
        return False
