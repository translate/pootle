# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

import pytest

from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.urls import reverse_lazy, reverse
from django.utils.safestring import mark_safe

from pytest_pootle.fixtures.models.user import TEST_USERS
from pytest_pootle.factories import LanguageDBFactory, TranslationProjectFactory

from pootle.core.delegate import formats
from pootle.core.paginator import paginate
from pootle.core.url_helpers import split_pootle_path
from pootle.core.views.admin import PootleAdminFormView, PootleAdminView
from pootle_app.models import PermissionSet
from pootle_app.views.admin.util import form_set_as_table
from pootle_language.models import Language
from pootle_project.models import PROJECT_CHECKERS, Project
from pootle_translationproject.models import TranslationProject


ADMIN_URL = reverse_lazy('pootle-admin')


@pytest.mark.django_db
def test_core_admin_view(request_users, rf):
    request = rf.get("/foo/bar")
    request.user = request_users["user"]
    if not request.user.is_superuser:
        with pytest.raises(PermissionDenied):
            PootleAdminView.as_view()(request)
    else:
        with pytest.raises(ImproperlyConfigured):
            # no template
            assert PootleAdminView.as_view()(request)


@pytest.mark.django_db
def test_core_admin_form_view(request_users, rf):
    request = rf.get("/foo/bar")
    request.user = request_users["user"]
    if not request.user.is_superuser:
        with pytest.raises(PermissionDenied):
            PootleAdminFormView.as_view()(request)
    else:
        with pytest.raises(TypeError):
            # no form
            assert PootleAdminFormView.as_view()(request)


def _test_admin_view(response, project):
    request = response.wsgi_request
    qs = TranslationProject.objects.filter(
        project=project).order_by('pootle_path')
    page = paginate(request, qs)

    url_kwargs = {
        'project_code': project.code,
        'dir_path': '',
        'filename': ''}

    assert page.number == response.context["objects"].number
    assert page.start_index() == response.context["objects"].start_index()
    assert page.end_index() == response.context["objects"].end_index()
    assert (
        list(response.context["objects"].object_list.values_list("pk", flat=True))
        == list(qs.values_list("pk", flat=True)))

    assert (
        response.context["formset"].__class__.__name__
        == "TranslationProjectFormFormSet")
    assert response.context["page"] == "admin-languages"
    assert response.context["browse_url"] == reverse(
        'pootle-project-browse',
        kwargs=url_kwargs)
    assert response.context["translate_url"] == reverse(
        'pootle-project-translate',
        kwargs=url_kwargs)
    assert (
        response.context['project']
        == {'code': project.code,
            'name': project.fullname,
            'treestyle': project.treestyle})
    assert (
        response.context["formset_text"]
        == mark_safe(
            form_set_as_table(
                response.context["formset"],
                lambda tp: (
                    u'<a href="%s">%s</a>'
                    % (reverse('pootle-tp-admin-permissions',
                               args=split_pootle_path(tp.pootle_path)[:2]),
                       tp.language)),
                "language")))


def _admin_view_get(client, project):
    return client.get(
        reverse(
            "pootle-project-admin-languages",
            kwargs=dict(project_code=project.code)))


def _admin_view_post(client, project, **kwargs):
    return client.post(
        reverse(
            "pootle-project-admin-languages",
            kwargs=dict(project_code=project.code)),
        kwargs)


@pytest.mark.django_db
def test_admin_not_logged_in(client):
    """Checks logged-out users cannot access the admin site."""
    response = client.get(ADMIN_URL)
    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_regular_user(client, default):
    """Checks regular users cannot access the admin site."""
    client.login(username=default.username, password='')
    response = client.get(ADMIN_URL)
    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_access(client):
    """Tests that admin users can access the admin site."""
    client.login(username="admin", password="admin")
    response = client.get(ADMIN_URL)
    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_view_project(client, request_users):
    user = request_users["user"]
    project = Project.objects.get(code="project0")

    client.login(
        username=user.username,
        password=request_users["password"])

    response = _admin_view_get(client, project)

    if not user.is_superuser:
        assert response.status_code == 403
        return
    _test_admin_view(response, project)


@pytest.mark.django_db
def test_admin_view_project_manager(client, member, administrate):
    project = Project.objects.get(code="project0")
    criteria = {
        'user': member,
        'directory': project.directory}
    ps = PermissionSet.objects.create(**criteria)
    ps.positive_permissions.set([administrate])
    client.login(
        username=member.username,
        password=TEST_USERS[member.username]["password"])
    response = _admin_view_get(client, project)
    assert response.status_code == 200
    _test_admin_view(response, project)
    response = _admin_view_post(client, project)
    assert response.status_code == 200
    _test_admin_view(response, project)


@pytest.mark.django_db
def test_admin_view_project_post(client, request_users):

    project = Project.objects.get(code="project0")
    user = request_users["user"]

    client.login(
        username=user.username,
        password=request_users["password"])

    if user.is_superuser:
        return
    response = _admin_view_post(client, project)
    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_view_project_add_tp(project_foo, english, client, admin):
    assert project_foo.treestyle != 'pootle_fs'
    user = admin

    new_language = LanguageDBFactory()
    TranslationProjectFactory(language=english, project=project_foo)

    client.login(
        username=user.username,
        password=TEST_USERS["admin"]["password"])

    get_response = _admin_view_get(client, project_foo)
    post_data = {}
    formset = get_response.context["formset"]
    forms = formset.forms + formset.extra_forms + [formset.management_form]

    for form in forms:
        for field in form.fields:
            post_data["%s-%s" % (form.prefix, field)] = (
                form.fields[field].initial
                or form.initial.get(field, ""))

    post_data["%s-language" % formset.extra_forms[0].prefix] = new_language.id
    post_data["%s-project" % formset.extra_forms[0].prefix] = project_foo.id

    response = _admin_view_post(client, project_foo, **post_data)

    new_tp = TranslationProject.objects.get(language=new_language,
                                            project=project_foo)
    assert new_tp in response.context["objects"].object_list

    _test_admin_view(response, project_foo)


@pytest.mark.django_db
def test_admin_view_project_add_pootle_fs_tp(project0, client, admin):
    assert project0.treestyle == 'pootle_fs'

    client.login(
        username=admin.username,
        password=TEST_USERS["admin"]["password"])

    get_response = _admin_view_get(client, project0)
    formset = get_response.context["formset"]
    assert len(formset.extra_forms) == 0


@pytest.mark.django_db
def test_admin_view_project_delete_tp(english, client, admin):

    user = admin
    project = Project.objects.get(code="project0")

    TranslationProject.objects.create(language=english, project=project)

    client.login(
        username=user.username,
        password=TEST_USERS["admin"]["password"])

    get_response = _admin_view_get(client, project)
    post_data = {}
    formset = get_response.context["formset"]
    forms = formset.forms + formset.extra_forms + [formset.management_form]

    for form in forms:
        for field in form.fields:
            post_data["%s-%s" % (form.prefix, field)] = (
                form.fields[field].initial
                or form.initial.get(field, ""))

    tp_pk = post_data["form-0-id"]
    post_data["form-0-DELETE"] = "true"
    response = _admin_view_post(client, project, **post_data)

    assert (
        tp_pk
        not in project.translationproject_set.values_list("pk", flat=True))

    _test_admin_view(response, project)


@pytest.mark.django_db
def test_admin_view_projects(client, request_users, english):
    user = request_users["user"]

    client.login(
        username=user.username,
        password=request_users["password"])

    response = client.get(
        reverse(
            "pootle-admin-projects"))

    if not user.is_superuser:
        assert response.status_code == 403
        return
    languages = Language.objects.exclude(code='templates')
    language_choices = [(lang.id, unicode(lang)) for lang in languages]
    filetypes = []
    for info in formats.get().values():
        filetypes.append(
            [info["pk"], info["display_title"]])
    project_checker_choices = [
        (checker, checker)
        for checker
        in sorted(PROJECT_CHECKERS.keys())]
    expected = {
        'page': 'admin-projects',
        'form_choices': {
            'checkstyle': project_checker_choices,
            'filetypes': filetypes,
            'source_language': language_choices,
            'treestyle': Project.treestyle_choices,
            'defaults': {
                'source_language': english.id}}}
    for k, v in expected.items():
        assert response.context_data[k] == v


@pytest.mark.django_db
def test_admin_view_project_add_tp_existing_dir(project0,
                                                english, client, admin):
    user = admin
    project0.treestyle = "nongnu"
    project0.save()
    new_language = LanguageDBFactory()
    client.login(
        username=user.username,
        password=TEST_USERS["admin"]["password"])
    get_response = _admin_view_get(client, project0)
    post_data = {}
    formset = get_response.context["formset"]
    forms = formset.forms + formset.extra_forms + [formset.management_form]
    os.makedirs(os.path.join(project0.get_real_path(), new_language.code))
    for form in forms:
        for field in form.fields:
            post_data["%s-%s" % (form.prefix, field)] = (
                form.fields[field].initial
                or form.initial.get(field, ""))
    post_data["%s-language" % formset.extra_forms[0].prefix] = new_language.id
    post_data["%s-project" % formset.extra_forms[0].prefix] = project0.id
    _admin_view_post(client, project0, **post_data)
    with pytest.raises(TranslationProject.DoesNotExist):
        TranslationProject.objects.get(
            language=new_language,
            project=project0)
