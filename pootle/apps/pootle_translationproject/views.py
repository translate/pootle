# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import functools

from django.conf import settings
from django.core.urlresolvers import resolve, reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache

from import_export.views import handle_upload_form
from pootle.core.browser import (
    get_parent, make_directory_item, make_store_item)
from pootle.core.decorators import get_path_obj, permission_required
from pootle.core.helpers import get_sidebar_announcements_context
from pootle.core.views import (
    PootleBrowseView, PootleExportView, PootleTranslateView)
from pootle_app.models import Directory
from pootle_app.models.permissions import (
    check_permission, get_matching_permissions)
from pootle_app.views.admin.permissions import admin_permissions as admin_perms
from pootle_language.models import Language
from pootle_store.models import Store

from .models import TranslationProject


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

            elif kwargs["dir_path"] or kwargs.get("filename", None):
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
        return self.object.translation_project

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
    export_url_path = "pootle-tp-export"
    translate_url_path = "pootle-tp-translate"

    @property
    def object_related(self):
        tp_prefix = (
            "parent__" * self.kwargs.get("dir_path", "").count("/"))
        return [
            "%stranslationproject" % tp_prefix,
            "%stranslationproject__language" % tp_prefix,
            "%stranslationproject__project" % tp_prefix]

    @lru_cache()
    def get_object(self):
        return get_object_or_404(
            Directory.objects.select_related(*self.object_related),
            pootle_path=self.path)

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
            self.object, self.request.user)


class TPStoreMixin(TPMixin):
    model = Store
    browse_url_path = "pootle-tp-store-browse"
    export_url_path = "pootle-tp-store-export"
    translate_url_path = "pootle-tp-store-translate"
    is_store = True

    @property
    def permission_context(self):
        return self.get_object().parent

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

    @lru_cache()
    def get_object(self):
        path = (
            "/%(language_code)s/%(project_code)s/%(dir_path)s%(filename)s"
            % self.kwargs)
        return get_object_or_404(
            Store.objects.select_related(
                "parent",
                "translation_project__language",
                "translation_project__project"),
            pootle_path=path)


class TPBrowseBaseView(PootleBrowseView):
    template_extends = 'translation_projects/base.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super(TPBrowseBaseView, self).get_context_data(*args, **kwargs)
        ctx.update(self.get_upload_widget())
        ctx.update(
            {'parent': get_parent(self.object)})
        return ctx

    def get_upload_widget(self):
        ctx = {}
        has_upload = (
            "import_export" in settings.INSTALLED_APPS
            and self.request.user.is_authenticated()
            and check_permission('translate', self.request))
        if has_upload:
            if "po" in self.project.filetype_tool.valid_extensions:
                ctx.update(handle_upload_form(
                    self.request,
                    self.project,
                    self.language))
            ctx.update(
                {'display_download': True,
                 'has_sidebar': True})
        return ctx

    def post(self, *args, **kwargs):
        return self.get(*args, **kwargs)


class TPBrowseStoreView(TPStoreMixin, TPBrowseBaseView):
    pass


class TPBrowseView(TPDirectoryMixin, TPBrowseBaseView):
    table_id = "tp"
    table_fields = [
        'name', 'progress', 'total', 'need-translation',
        'suggestions', 'critical', 'last-updated', 'activity']

    @cached_property
    def items(self):
        dirs_with_vfolders = []
        if 'virtualfolder' in settings.INSTALLED_APPS:
            stores = self.tp.stores.filter(
                pootle_path__startswith=self.object.pootle_path)
            vf_stores = stores.filter(
                vfolders__isnull=False).exclude(parent=self.object)
            dirs_with_vfolders = set(
                path.replace(self.object.pootle_path, "").split("/")[0]
                for path
                in vf_stores.values_list(
                    "pootle_path", flat=True))
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
        return directories + stores

    @cached_property
    def has_vfolders(self):
        return self.stats["vfolders"] and True or False

    @cached_property
    def stats(self):
        stats = (
            {}
            if not self.vfolders_data_view
            else self.vfolders_data_view.stats)
        stats.update(self.object.data_tool.get_stats(user=self.request.user))
        return stats

    def get_context_data(self, *args, **kwargs):
        ctx = super(TPBrowseView, self).get_context_data(*args, **kwargs)
        if self.vfolders_data_view:
            ctx.update(self.vfolders_data_view.table_data)
        return ctx


class TPTranslateBaseView(PootleTranslateView):
    translate_url_path = "pootle-tp-translate"
    browse_url_path = "pootle-tp-browse"
    export_url_path = "pootle-tp-export"
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


class TPExportBaseView(PootleExportView):

    @property
    def source_language(self):
        return self.project.source_language


class TPExportView(TPDirectoryMixin, TPExportBaseView):
    pass


class TPExportStoreView(TPStoreMixin, TPExportBaseView):
    pass
