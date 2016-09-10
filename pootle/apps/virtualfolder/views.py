# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from pootle.core.delegate import search_backend
from pootle.core.exceptions import Http400
from pootle.core.http import JsonResponse
from pootle.core.url_helpers import get_path_parts
from pootle.i18n.gettext import ugettext as _
from pootle_misc.util import ajax_required
from pootle_store.forms import UnitSearchForm
from pootle_store.unit.results import GroupedResults
from pootle_translationproject.views import TPTranslateView

from .models import VirtualFolder


class VFolderTPTranslateView(TPTranslateView):
    display_vfolder_priority = False

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
