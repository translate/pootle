# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property

from pootle.core.browser import get_table_headings
from pootle.core.delegate import search_backend
from pootle.core.exceptions import Http400
from pootle.core.http import JsonResponse
from pootle.core.url_helpers import get_path_parts, split_pootle_path
from pootle.i18n.gettext import ugettext as _
from pootle_misc.util import ajax_required
from pootle_store.forms import UnitSearchForm
from pootle_store.unit.results import GroupedResults
from pootle_translationproject.views import TPTranslateView

from .delegate import vfolders_data_tool
from .display import VFolderStatsDisplay
from .models import VirtualFolder


def make_vfolder_dict(context, vf, stats):
    lang_code, proj_code = split_pootle_path(context.pootle_path)[:2]
    base_url = reverse(
        "pootle-vfolder-tp-translate",
        kwargs=dict(
            vfolder_name=vf,
            language_code=lang_code,
            project_code=proj_code))
    return {
        'href_translate': base_url,
        'title': stats["title"],
        'code': vf,
        'priority': stats.get("priority"),
        'is_grayed': not stats["isVisible"],
        'stats': stats,
        'icon': 'vfolder'}


class VFolderTPTranslateView(TPTranslateView):
    display_vfolder_priority = False

    @cached_property
    def check_data(self):
        return self.vfolders_data_view.vfolder_data_tool.get_checks(
            user=self.request.user).get(self.vfolder_pk, {})

    @cached_property
    def vfolder(self):
        return VirtualFolder.objects.get(name=self.kwargs["vfolder_name"])

    @property
    def vfolder_pk(self):
        return self.vfolder.pk

    def get_context_data(self, *args, **kwargs):
        ctx = super(
            VFolderTPTranslateView,
            self).get_context_data(*args, **kwargs)
        ctx["unit_api_root"] = reverse(
            "vfolder-pootle-xhr-units",
            kwargs=dict(vfolder_name=self.vfolder.name))
        ctx["resource_path"] = (
            "/".join(
                ["++vfolder",
                 self.vfolder.name,
                 self.object.pootle_path.replace(self.ctx_path, "")]))
        ctx["resource_path_parts"] = get_path_parts(ctx["resource_path"])
        return ctx


@ajax_required
def get_vfolder_units(request, **kwargs):
    """Gets source and target texts and its metadata.

    :return: A JSON-encoded string containing the source and target texts
        grouped by the store they belong to.

        The optional `count` GET parameter defines the chunk size to
        consider. The user's preference will be used by default.

        When the `initial` GET parameter is present, a sorted list of
        the result set ids will be returned too.
    """
    search_form = UnitSearchForm(request.GET, user=request.user)

    vfolder = get_object_or_404(
        VirtualFolder,
        name=kwargs.get("vfolder_name"))

    if not search_form.is_valid():
        errors = search_form.errors.as_data()
        if "path" in errors:
            for error in errors["path"]:
                if error.code == "max_length":
                    raise Http400(_('Path too long.'))
                elif error.code == "required":
                    raise Http400(_('Arguments missing.'))
        raise Http404(forms.ValidationError(search_form.errors).messages)

    search_form.cleaned_data["vfolder"] = vfolder
    backend = search_backend.get(VirtualFolder)(
        request.user, **search_form.cleaned_data)
    total, start, end, units_qs = backend.search()
    return JsonResponse(
        {'start': start,
         'end': end,
         'total': total,
         'unitGroups': GroupedResults(units_qs).data})


class VFoldersDataView(object):

    _table_fields = (
        'name', 'progress', 'activity',
        'total', 'need-translation',
        'suggestions', 'critical', 'priority')

    def __init__(self, context, user, has_admin_access=False):
        self.context = context
        self.user = user
        self.has_admin_access = has_admin_access

    @cached_property
    def vfolder_data_tool(self):
        return vfolders_data_tool.get(self.context.__class__)(self.context)

    @property
    def table_fields(self):
        fields = self._table_fields
        if self.has_admin_access:
            fields += ('last-updated', )
        return fields

    @cached_property
    def table_data(self):
        ctx = {}
        if len(self.all_stats) > 0:
            ctx.update({
                'children': {
                    'id': 'vfolders',
                    'fields': self.table_fields,
                    'headings': get_table_headings(self.table_fields),
                    'rows': self.table_items}})
        return ctx

    @cached_property
    def all_stats(self):
        return VFolderStatsDisplay(
            self.context,
            self.vfolder_data_tool.get_stats(user=self.user)).stats

    @cached_property
    def stats(self):
        return dict(children=self.all_stats)

    @property
    def table_items(self):
        items = [make_vfolder_dict(self.context, *vf)
                 for vf
                 in self.all_stats.items()]
        items.sort(
            lambda x, y: cmp(y['stats']['priority'], x['stats']['priority']))
        return items

    @cached_property
    def has_data(self):
        return (
            self.vfolder_data_tool.all_stat_data.exists()
            if self.vfolder_data_tool.show_all_to(self.user)
            else self.vfolder_data_tool.stat_data.exists())
