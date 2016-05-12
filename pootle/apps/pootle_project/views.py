# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import locale

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.utils.html import escape
from django.utils.lru_cache import lru_cache
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from pootle.core.browser import (
    make_language_item, make_project_list_item, make_xlanguage_item)
from pootle.core.decorators import get_path_obj, permission_required
from pootle.core.helpers import get_sidebar_announcements_context
from pootle.core.paginator import paginate
from pootle.core.url_helpers import split_pootle_path
from pootle.core.views import (
    PootleAdminView, PootleDetailView, PootleBrowseView, PootleExportView,
    PootleTranslateView, set_permissions, requires_permission)
from pootle_app.models import Directory
from pootle_app.views.admin import util
from pootle_app.views.admin.permissions import admin_permissions
from pootle_project.forms import TranslationProjectForm
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject

from .forms import TranslationProjectFormSet
from .models import Project, ProjectSet, ProjectResource


class ProjectMixin(object):
    model = Project
    browse_url_path = "pootle-project-browse"
    export_url_path = "pootle-project-export"
    translate_url_path = "pootle-project-translate"
    template_extends = 'projects/base.html'

    @property
    def ctx_path(self):
        return "/projects/%s/" % self.project.code

    @property
    def permission_context(self):
        return self.project.directory

    @cached_property
    def project(self):
        project = get_object_or_404(
            Project.objects.select_related("directory"),
            code=self.kwargs["project_code"])
        if project.disabled and not self.request.user.is_superuser:
            raise Http404
        return project

    @property
    def url_kwargs(self):
        return {
            "project_code": self.project.code,
            "dir_path": self.kwargs["dir_path"],
            "filename": self.kwargs["filename"]}

    @lru_cache()
    def get_object(self):
        if not (self.kwargs["dir_path"] or self.kwargs["filename"]):
            return self.project

        project_path = (
            "/%s/%s%s"
            % (self.project.code,
               self.kwargs['dir_path'],
               self.kwargs['filename']))
        regex = r"^/[^/]*%s$" % project_path
        if not self.kwargs["filename"]:
            dirs = Directory.objects.live()
            if self.kwargs['dir_path'].count("/"):
                tp_prefix = "parent__" * self.kwargs['dir_path'].count("/")
                dirs = dirs.select_related(
                    "%stranslationproject" % tp_prefix,
                    "%stranslationproject__language" % tp_prefix)
            resources = (
                dirs.exclude(pootle_path__startswith="/templates")
                    .filter(pootle_path__endswith=project_path)
                    .filter(pootle_path__regex=regex))
        else:
            resources = (
                Store.objects.live()
                             .select_related("translation_project__language")
                             .filter(translation_project__project=self.project)
                             .filter(pootle_path__endswith=project_path)
                             .filter(pootle_path__regex=regex))
        if resources:
            return ProjectResource(
                resources,
                ("/projects/%(project_code)s/%(dir_path)s%(filename)s"
                 % self.kwargs))
        raise Http404

    @property
    def resource_path(self):
        return "%(dir_path)s%(filename)s" % self.kwargs


class ProjectBrowseView(ProjectMixin, PootleBrowseView):
    table_id = "project"
    table_fields = [
        'name', 'progress', 'total', 'need-translation',
        'suggestions', 'critical', 'last-updated', 'activity']

    @property
    def stats(self):
        return self.object.get_stats_for_user(
            self.request.user)

    @property
    def pootle_path(self):
        return self.object.pootle_path

    @property
    def permission_context(self):
        return self.project.directory

    @cached_property
    def sidebar_announcements(self):
        return get_sidebar_announcements_context(
            self.request,
            (self.project, ))

    @property
    def url_kwargs(self):
        return self.kwargs

    @cached_property
    def items(self):
        item_func = (
            make_xlanguage_item
            if (self.kwargs['dir_path']
                or self.kwargs['filename'])
            else make_language_item)

        items = [
            item_func(item)
            for item
            in self.object.get_children_for_user(self.request.user)
        ]

        items.sort(
            lambda x, y: locale.strcoll(x['title'], y['title']))

        return items


class ProjectTranslateView(ProjectMixin, PootleTranslateView):

    @set_permissions
    @requires_permission("administrate")
    def dispatch(self, request, *args, **kwargs):
        return super(PootleDetailView, self).dispatch(request, *args, **kwargs)

    @property
    def pootle_path(self):
        return self.object.pootle_path


class ProjectExportView(ProjectMixin, PootleExportView):
    source_language = "en"


class ProjectAdminView(PootleAdminView):

    model = Project
    slug_field = 'code'
    slug_url_kwarg = 'project_code'
    template_name = 'projects/admin/languages.html'

    msg_form_error = _(
        "There are errors in the form. Please review "
        "the problems below.")

    model_formset_class = TranslationProject
    form_class = TranslationProjectForm
    msg = ""

    @cached_property
    def formset_class(self):
        return modelformset_factory(
            self.model_formset_class,
            formset=TranslationProjectFormSet,
            form=self.form_class,
            **dict(
                can_delete=True,
                extra=self.formset_extra,
                fields=["language", "project"]))

    @property
    def formset_extra(self):
        return (
            (self.object.get_template_translationproject() is not None)
            and 1 or 0)

    @property
    def form_initial(self):
        return [dict(project=self.object.pk)]

    @property
    def page(self):
        return paginate(self.request, self.qs)

    @property
    def qs(self):
        return self.model_formset_class.objects.filter(
            project=self.object).order_by('pootle_path')

    @property
    def response_url(self):
        return self.request.build_absolute_uri('/')

    @property
    def url_kwargs(self):
        return {
            'project_code': self.object.code,
            'dir_path': '',
            'filename': ''}

    def get_context_data(self, *la, **kwa):
        if self.request.method == 'POST' and self.request.POST:
            self.process_formset()

        formset = self.get_formset()
        return {
            'page': 'admin-languages',
            'browse_url': (
                reverse(
                    'pootle-project-browse',
                    kwargs=self.url_kwargs)),
            'translate_url': (
                reverse(
                    'pootle-project-translate',
                    kwargs=self.url_kwargs)),
            'project': {
                'code': self.object.code,
                'name': self.object.fullname},
            'formset_text': self.render_formset(formset),
            'formset': formset,
            'objects': self.page,
            'error_msg': self.msg,
            'can_add': self.formset_extra}

    def get_formset(self, post=None):
        return self.formset_class(
            post,
            initial=self.form_initial,
            queryset=self.page.object_list,
            response_url=self.response_url)

    def process_formset(self):
        formset = self.get_formset(self.request.POST)
        if formset.is_valid():
            formset.save()
            for tp in formset.new_objects:
                messages.add_message(
                    self.request,
                    messages.INFO,
                    _("Translation project (%s) has been created. We are "
                      "now updating its stores from file templates." % tp))

            for tp in formset.deleted_objects:
                messages.add_message(
                    self.request,
                    messages.INFO,
                    _("Translation project (%s) has been deleted" % tp))
        else:
            messages.add_message(self.request, messages.ERROR,
                                 self.msg_form_error)

    def render_formset(self, formset):

        def generate_link(tp):
            path_args = split_pootle_path(tp.pootle_path)[:2]
            perms_url = reverse('pootle-tp-admin-permissions', args=path_args)
            return u'<a href="%s">%s</a>' % (perms_url, escape(tp.language))
        return mark_safe(
            util.form_set_as_table(
                formset,
                generate_link,
                "language"))


@get_path_obj
@permission_required('administrate')
def project_admin_permissions(request, project):
    ctx = {
        'page': 'admin-permissions',

        'browse_url': reverse('pootle-project-browse', kwargs={
            'project_code': project.code,
            'dir_path': '',
            'filename': '',
        }),
        'translate_url': reverse('pootle-project-translate', kwargs={
            'project_code': project.code,
            'dir_path': '',
            'filename': '',
        }),

        'project': project,
        'directory': project.directory,
    }

    return admin_permissions(request, project.directory,
                             'projects/admin/permissions.html', ctx)


class ProjectsMixin(object):
    template_extends = 'projects/all/base.html'
    browse_url_path = "pootle-projects-browse"
    export_url_path = "pootle-projects-export"
    translate_url_path = "pootle-projects-translate"

    @lru_cache()
    def get_object(self):
        user_projects = (
            Project.objects.for_user(self.request.user)
                           .select_related("directory__pootle_path"))
        return ProjectSet(user_projects)

    @property
    def permission_context(self):
        return self.get_object().directory

    @property
    def has_admin_access(self):
        return self.request.user.is_superuser

    @property
    def url_kwargs(self):
        return {}


class ProjectsBrowseView(ProjectsMixin, PootleBrowseView):
    table_id = "projects"
    table_fields = [
        'name', 'progress', 'total', 'need-translation',
        'suggestions', 'critical', 'last-updated', 'activity']

    @cached_property
    def items(self):
        items = [
            make_project_list_item(project)
            for project
            in self.object.children]
        items.sort(
            lambda x, y: locale.strcoll(x['title'], y['title']))
        return items

    @property
    def sidebar_announcements(self):
        return {}, None

    def get(self, *args, **kwargs):
        response = super(ProjectsBrowseView, self).get(*args, **kwargs)
        response.set_cookie('pootle-language', "projects")
        return response


class ProjectsTranslateView(ProjectsMixin, PootleTranslateView):

    @set_permissions
    @requires_permission("administrate")
    def dispatch(self, request, *args, **kwargs):
        return super(PootleDetailView, self).dispatch(request, *args, **kwargs)


class ProjectsExportView(ProjectsMixin, PootleExportView):
    source_language = "en"
