# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import functools

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import resolve, reverse
from django.utils.functional import cached_property

from pootle.core.browser import (
    get_parent, make_directory_item, make_store_item)
from pootle.core.decorators import (
    get_path_obj, permission_required, persistent_property)
from pootle.core.helpers import get_sidebar_announcements_context
from pootle.core.views import PootleBrowseView, PootleTranslateView
from pootle.core.views.display import StatsDisplay
from pootle.core.views.paths import PootlePathsJSON
from pootle_app.models import Directory
from pootle_app.models.permissions import get_matching_permissions
from pootle_app.views.admin.permissions import admin_permissions as admin_perms
from pootle_language.models import Language
from pootle_store.models import Store

from .apps import PootleTPConfig
from .models import TranslationProject


class TPPathsJSON(PootlePathsJSON):

    @cached_property
    def context(self):
        return get_object_or_404(
            TranslationProject.objects.all(),
            language__code=self.kwargs["language_code"],
            project__code=self.kwargs["project_code"])


@get_path_obj
@permission_required('administrate')
def admin_permissions(request, translation_project):
    ctx = {
        'page': 'admin-permissions',

        'browse_url': reverse('pootle-tp-browse', kwargs={
            'language_code': translation_project.language.code,
            'project_code': translation_project.project.code,
        }),
        'translate_url': reverse('pootle-tp-translate', kwargs={
            'language_code': translation_project.language.code,
            'project_code': translation_project.project.code,
        }),

        'translation_project': translation_project,
        'project': translation_project.project,
        'language': translation_project.language,
        'directory': translation_project.directory,
    }
    return admin_perms(request, translation_project.directory,
                       'translation_projects/admin/permissions.html', ctx)


def redirect_to_tp_on_404(f):

    @functools.wraps(f)
    def method_wrapper(self, request, *args, **kwargs):
        try:
            request.permissions = get_matching_permissions(
                request.user,
                self.permission_context) or []
        except Http404 as e:
            # Test if lang code is not canonical but valid
            lang = Language.get_canonical(kwargs['language_code'])
            if lang is not None and lang.code != kwargs['language_code']:
                kwargs["language_code"] = lang.code
                return redirect(
                    resolve(request.path).view_name,
                    permanent=True,
                    **kwargs)

            elif kwargs.get("dir_path", None) or kwargs.get("filename", None):
                try:
                    TranslationProject.objects.get(
                        project__code=kwargs["project_code"],
                        language__code=kwargs["language_code"])
                    # the TP exists so redirect to it
                    return redirect(
                        reverse(
                            'pootle-tp-browse',
                            kwargs={
                                k: v
                                for k, v
                                in kwargs.items()
                                if k in [
                                    "language_code",
                                    "project_code"]}))
                except TranslationProject.DoesNotExist:
                    pass

            # if we get here - the TP does not exist
            user_choice = self.request.COOKIES.get(
                'user-choice', None)
            if user_choice:
                url = None
                if user_choice == 'language':
                    url = reverse(
                        'pootle-language-browse',
                        args=[kwargs["language_code"]])
                elif user_choice == "project":
                    url = reverse(
                        'pootle-project-browse',
                        args=[kwargs["project_code"], '', ''])
                if url:
                    response = redirect(url)
                    response.delete_cookie('user-choice')
                    return response
            raise e
        return f(self, request, *args, **kwargs)
    return method_wrapper


class TPMixin(object):
    """This Mixin is used by all TP views.

    The context object may be a resource with the TP, ie a Directory or Store.
    """

    ns = "pootle.tp"
    sw_version = PootleTPConfig.version

    @redirect_to_tp_on_404
    def dispatch(self, request, *args, **kwargs):
        return super(TPMixin, self).dispatch(request, *args, **kwargs)

    @property
    def ctx_path(self):
        return self.tp.pootle_path

    @property
    def resource_path(self):
        return self.object.pootle_path.replace(self.ctx_path, "")

    @property
    def dir_path(self):
        return self.resource_path

    @cached_property
    def tp(self):
        if not self.object.tp:
            return self.object.translation_project
        return self.object.tp

    @cached_property
    def project(self):
        if self.tp.project.disabled and not self.request.user.is_superuser:
            raise Http404
        return self.tp.project

    @cached_property
    def language(self):
        return self.tp.language

    @cached_property
    def sidebar_announcements(self):
        return get_sidebar_announcements_context(
            self.request,
            (self.project, self.language, self.tp))


class TPDirectoryMixin(TPMixin):
    model = Directory
    browse_url_path = "pootle-tp-browse"
    translate_url_path = "pootle-tp-translate"

    @property
    def object_related(self):
        return [
            "parent",
            "tp",
            "tp__language",
            "tp__language__directory",
            "tp__project"]

    @cached_property
    def object(self):
        return get_object_or_404(
            Directory.objects.select_related(*self.object_related),
            pootle_path=self.path)

    def get_object(self):
        return self.object

    @property
    def url_kwargs(self):
        return {
            "language_code": self.language.code,
            "project_code": self.project.code,
            "dir_path": self.dir_path}

    @cached_property
    def vfolders_data_view(self):
        if 'virtualfolder' not in settings.INSTALLED_APPS:
            return
        from virtualfolder.delegate import vfolders_data_view

        return vfolders_data_view.get(self.object.__class__)(
            self.object, self.request.user, self.has_admin_access)


class TPStoreMixin(TPMixin):
    model = Store
    browse_url_path = "pootle-tp-store-browse"
    translate_url_path = "pootle-tp-store-translate"
    is_store = True
    panels = ()

    @property
    def permission_context(self):
        return self.get_object().parent

    @cached_property
    def tp(self):
        return self.object.translation_project

    @property
    def dir_path(self):
        return self.resource_path.replace(self.object.name, "")

    @property
    def url_kwargs(self):
        return {
            "language_code": self.language.code,
            "project_code": self.project.code,
            "dir_path": self.dir_path,
            "filename": self.object.name}

    def get_object(self):
        return self.object

    @cached_property
    def object(self):
        path = (
            "/%(language_code)s/%(project_code)s/%(dir_path)s%(filename)s"
            % self.kwargs)
        return get_object_or_404(
            Store.objects.select_related(
                "parent",
                "data",
                "data__last_submission",
                "data__last_submission__unit",
                "data__last_submission__unit__store",
                "data__last_submission__unit__store__parent",
                "data__last_created_unit",
                "data__last_created_unit__store",
                "translation_project__directory",
                "translation_project__language",
                "translation_project__language__directory",
                "translation_project__project"),
            pootle_path=path)


class TPBrowseBaseView(PootleBrowseView):
    template_extends = 'translation_projects/base.html'

    def get_context_data(self, *args, **kwargs):
        upload_widget = self.get_upload_widget()
        ctx = super(TPBrowseBaseView, self).get_context_data(*args, **kwargs)
        ctx.update(upload_widget)
        ctx.update(
            {'parent': get_parent(self.object)})
        return ctx

    @property
    def can_upload(self):
        return (
            "import_export" in settings.INSTALLED_APPS
            and self.request.user.is_authenticated
            and (self.request.user.is_superuser
                 or "translate" in self.request.permissions
                 or "administrate" in self.request.permissions))

    def get_upload_widget(self):
        ctx = {}
        if self.can_upload:
            from import_export.views import handle_upload_form

            ctx.update(handle_upload_form(self.request, self.tp))
            ctx.update(
                {'display_download': True,
                 'has_sidebar': True})
        return ctx

    def post(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    @property
    def score_context(self):
        return self.tp


class TPBrowseStoreView(TPStoreMixin, TPBrowseBaseView):

    disabled_items = False

    @property
    def cache_key(self):
        return ""


class TPBrowseView(TPDirectoryMixin, TPBrowseBaseView):
    view_name = "tp"
    panel_names = ('vfolders', 'children')

    @property
    def path(self):
        kwargs = self.kwargs
        kwargs["dir_path"] = kwargs.get("dir_path", "")
        kwargs["filename"] = kwargs.get("filename", "")
        return (
            "/%(language_code)s/%(project_code)s/%(dir_path)s%(filename)s"
            % kwargs)

    @persistent_property
    def object_children(self):
        dirs_with_vfolders = []
        if 'virtualfolder' in settings.INSTALLED_APPS:
            stores = self.tp.stores
            if self.object.tp_path != "/":
                stores = stores.filter(
                    tp_path__startswith=self.object.tp_path)
            vf_stores = stores.filter(
                vfolders__isnull=False).exclude(parent=self.object)
            dirs_with_vfolders = set(
                [path.replace(self.object.pootle_path, "").split("/")[0]
                 for path
                 in vf_stores.values_list(
                     "pootle_path", flat=True)])
        directories = [
            make_directory_item(
                child,
                **(dict(sort="priority")
                   if child.name in dirs_with_vfolders
                   else {}))
            for child in self.object.children
            if isinstance(child, Directory)]
        stores = [
            make_store_item(child)
            for child in self.object.children
            if isinstance(child, Store)]
        return self.add_child_stats(directories + stores)

    @cached_property
    def has_vfolders(self):
        vfdata = self.vfolders_data_view
        return bool(
            vfdata
            and vfdata.table_data
            and vfdata.table_data.get("children"))

    @cached_property
    def stats(self):
        stats_ob = (
            self.object.tp
            if self.object.tp_path == "/"
            else self.object)
        return StatsDisplay(
            stats_ob,
            stats=stats_ob.data_tool.get_stats(
                user=self.request.user)).stats


class TPTranslateBaseView(PootleTranslateView):
    translate_url_path = "pootle-tp-translate"
    browse_url_path = "pootle-tp-browse"
    template_extends = 'translation_projects/base.html'

    @property
    def pootle_path(self):
        return "%s%s" % (self.ctx_path, self.resource_path)


class TPTranslateView(TPDirectoryMixin, TPTranslateBaseView):

    @property
    def request_path(self):
        return "/%(language_code)s/%(project_code)s/%(dir_path)s" % self.kwargs

    @cached_property
    def display_vfolder_priority(self):
        return self.vfolders_data_view.has_data

    @property
    def path(self):
        return self.request_path


class TPTranslateStoreView(TPStoreMixin, TPTranslateBaseView):
    pass
