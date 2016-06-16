# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.urlresolvers import reverse_lazy, reverse
from django.utils.safestring import mark_safe

from pytest_pootle.env import TEST_USERS
from pytest_pootle.factories import LanguageDBFactory

from pootle.core.paginator import paginate
from pootle.core.url_helpers import split_pootle_path
from pootle_app.models import PermissionSet
from pootle_app.views.admin.util import form_set_as_table
from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject


ADMIN_URL = reverse_lazy('pootle-admin')


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
            'name': project.fullname})
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
def test_admin_view_projects(client, request_users):
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
def test_admin_view_projects_manager(client, member, administrate):
    project = Project.objects.get(code="project0")
    criteria = {
        'user': member,
        'directory': project.directory}
    ps = PermissionSet.objects.create(**criteria)
    ps.positive_permissions = [administrate]
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
def test_admin_view_projects_post(client, request_users):

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
def test_admin_view_projects_add_tp(english, client, admin):

    user = admin
    project = Project.objects.get(code="project0")

    new_language = LanguageDBFactory()
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

    post_data["%s-language" % formset.extra_forms[0].prefix] = new_language.id
    post_data["%s-project" % formset.extra_forms[0].prefix] = project.id

    response = _admin_view_post(client, project, **post_data)

    new_tp = TranslationProject.objects.get(language=new_language, project=project)
    assert new_tp in response.context["objects"].object_list

    _test_admin_view(response, project)


@pytest.mark.django_db
def test_admin_view_projects_delete_tp(english, client, admin):

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
