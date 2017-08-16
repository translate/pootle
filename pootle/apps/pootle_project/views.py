# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib import messages
from django.forms.models import modelformset_factory
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.html import escape
from django.utils.lru_cache import lru_cache
from django.utils.safestring import mark_safe

from pootle.core.browser import (
    make_language_item, make_project_list_item, make_xlanguage_item)
from pootle.core.decorators import (
    get_path_obj, permission_required, persistent_property)
from pootle.core.helpers import get_sidebar_announcements_context
from pootle.core.paginator import paginate
from pootle.core.url_helpers import split_pootle_path
from pootle.core.views import (
    PootleAdminView, PootleBrowseView, PootleTranslateView)
from pootle.core.views.paths import PootlePathsJSON
from pootle.i18n.gettext import ugettext as _
from pootle_app.models import Directory
from pootle_app.views.admin import util
from pootle_app.views.admin.permissions import admin_permissions
from pootle_misc.util import cmp_by_last_activity
from pootle_project.forms import TranslationProjectForm
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject

from .apps import PootleProjectConfig
from .forms import TranslationProjectFormSet
from .models import Project, ProjectResource, ProjectSet


class ProjectPathsJSON(PootlePathsJSON):

    @cached_property
    def context(self):
        return get_object_or_404(
            Project.objects.all(),
            code=self.kwargs["project_code"])


class ProjectMixin(object):
    ns = "pootle.project"
    sw_version = PootleProjectConfig.version
    model = Project
    browse_url_path = "pootle-project-browse"
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

    @cached_property
    def cache_key(self):
        return (
            "%s.%s.%s.%s::%s.%s.%s"
            % (self.page_name,
               self.view_name,
               self.project.data_tool.cache_key,
               self.kwargs["dir_path"],
               self.kwargs["filename"],
               self.show_all,
               self.request_lang))

    @property
    def url_kwargs(self):
        return {
            "project_code": self.project.code,
            "dir_path": self.kwargs["dir_path"],
            "filename": self.kwargs["filename"]}

    def get_object(self):
        return self.object

    @cached_property
    def object(self):
        return self.object_with_children

    @persistent_property
    def object_with_children(self):
        if not (self.kwargs["dir_path"] or self.kwargs["filename"]):
            return self.project

        tp_path = (
            "/%s%s"
            % (self.kwargs['dir_path'],
               self.kwargs['filename']))
        if not self.kwargs["filename"]:
            dirs = Directory.objects.live().filter(tp__project=self.project)
            if self.kwargs['dir_path'].count("/"):
                dirs = dirs.select_related(
                    "parent",
                    "tp",
                    "tp__language")
            resources = (
                dirs.filter(tp_path=tp_path))
        else:
            resources = (
                Store.objects.live()
                             .select_related("translation_project__language")
                             .filter(translation_project__project=self.project)
                             .filter(tp_path=tp_path))
        if resources:
            return ProjectResource(
                resources,
                ("/projects/%(project_code)s/%(dir_path)s%(filename)s"
                 % self.kwargs),
                context=self.project)
        raise Http404

    @property
    def resource_path(self):
        return "%(dir_path)s%(filename)s" % self.kwargs


class ProjectBrowseView(ProjectMixin, PootleBrowseView):
    view_name = "project"

    @property
    def is_templates_context(self):
        # this view is a "template context" only when
        # its a single .pot file or similar
        return (
            len(self.object_children) == 1
            and self.object_children[0]["code"] == "templates")

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
    def score_context(self):
        return self.project

    @property
    def url_kwargs(self):
        return self.kwargs

    @cached_property
    def object_children(self):
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

        items = self.add_child_stats(items)
        items.sort(cmp_by_last_activity)
        return items


class ProjectTranslateView(ProjectMixin, PootleTranslateView):
    required_permission = "administrate"

    @property
    def pootle_path(self):
        return self.object.pootle_path


class ProjectAdminView(PootleAdminView):

    queryset = Project.objects.select_related("directory")
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
        can_add = (
            self.object.treestyle != 'pootle_fs'
            and self.object.get_template_translationproject() is not None)

        return can_add and 1 or 0

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

    def get_context_data(self, **kwargs_):
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
                'name': self.object.fullname,
                'treestyle': self.object.treestyle},
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
                      "now updating its files from file templates." % tp))

            for tp in formset.deleted_objects:
                messages.add_message(
                    self.request,
                    messages.INFO,
                    _("Translation project (%s) has been deleted" % tp))
        else:
            for form in formset:
                for error in form.errors.values():
                    messages.add_message(
                        self.request,
                        messages.ERROR,
                        error)

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
    ns = "pootle.project"
    sw_version = PootleProjectConfig.version
    template_extends = 'projects/all/base.html'
    browse_url_path = "pootle-projects-browse"
    translate_url_path = "pootle-projects-translate"

    @lru_cache()
    def get_object(self):
        user_projects = (
            Project.objects.for_user(self.request.user)
                           .select_related("directory"))
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
    view_name = "projects"

    @cached_property
    def object_children(self):
        items = [
            make_project_list_item(project)
            for project
            in self.object.children]
        items = self.add_child_stats(items)
        items.sort(cmp_by_last_activity)
        return items

    @property
    def sidebar_announcements(self):
        return {}

    def get(self, *args, **kwargs):
        response = super(ProjectsBrowseView, self).get(*args, **kwargs)
        response.set_cookie('pootle-language', "projects")
        return response


class ProjectsTranslateView(ProjectsMixin, PootleTranslateView):
    required_permission = "administrate"
