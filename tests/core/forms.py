# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django import forms

from pootle.core.forms import FormtableForm
from pootle_store.models import Unit
from pootle_project.models import Project


class DummyFormtableForm(FormtableForm):
    search_field = "units"
    units = forms.ModelMultipleChoiceField(
        Unit.objects.order_by("id"),
        required=False)


class DummySearchFormtableForm(DummyFormtableForm):
    filter_project = forms.ModelChoiceField(
        Project.objects.all(),
        required=False)

    def search(self):
        qs = self.fields[self.search_field].queryset
        project = self._search_filters.get("filter_project")
        if project:
            return qs.filter(
                store__translation_project__project=project)
        return qs


@pytest.mark.django_db
def test_form_formtable():
    form = DummyFormtableForm()
    assert form.should_save() is False
    assert form.action_field == "actions"
    assert form.comment_field == "comment"
    assert form.select_all_field == "select_all"
    assert sorted(form.fields.keys()) == [
        "actions", "comment",
        "page_no", "results_per_page", "select_all", "units"]
    assert list(form.search()) == list(Unit.objects.order_by("id"))
    assert form.fields["results_per_page"].initial == 10
    assert form.fields["page_no"].initial == 1


@pytest.mark.django_db
def test_form_formtable_search_filters():
    form = DummySearchFormtableForm(
        data=dict(results_per_page=10, page_no=1))
    assert form.is_valid()
    assert form.cleaned_data["page_no"] == 1
    assert form.cleaned_data["results_per_page"] == 10
    assert list(form.search()) == list(Unit.objects.order_by("id"))

    # filter by project
    project = Project.objects.first()
    form = DummySearchFormtableForm(
        data=dict(filter_project=project.pk))
    assert form.is_valid()
    assert form.cleaned_data["page_no"] == 1
    assert form.cleaned_data["results_per_page"] == 10

    # results are filtered and field queryset is also limited
    assert (
        list(form.search())
        == list(form.fields["units"].queryset.all())
        == list(
            Unit.objects.filter(
                store__translation_project__project=project).order_by("id")))


def _test_batch(form, units):
    batch = form.batch()
    assert batch.number == form._page_no
    units_count = form.fields["units"].queryset.count()
    assert (
        batch.paginator.num_pages
        == ((units_count / form._results_per_page)
            + (1
               if units_count % form._results_per_page
               else 0)))
    assert (
        [unit.id for unit in batch.object_list]
        == list(
            units.values_list("id", flat=True)[
                form._results_per_page * (form._page_no - 1): (
                    form._results_per_page * form._page_no)]))


@pytest.mark.django_db
def test_form_formtable_bad():
    with pytest.raises(ValueError):
        # the base form does not specify a search field
        FormtableForm()

    form = DummySearchFormtableForm()
    unit_id = form.fields["units"].queryset.first().pk
    project = form.fields["filter_project"].queryset.first()
    project_units = Unit.objects.filter(
        store__translation_project__project=project).order_by("id")

    # now submit the form with units set but no action
    form = DummySearchFormtableForm(data=dict(units=[unit_id]))
    assert not form.is_valid()
    assert form.errors.keys() == ["actions"]
    _test_batch(form, Unit.objects.order_by("id"))
    assert form._page_no == 1
    assert form._results_per_page == 10
    assert form.fields["page_no"].initial == 1
    assert form.fields["results_per_page"].initial == 10

    # submit the form with filters, form is not valid but filters work
    form = DummySearchFormtableForm(
        data=dict(
            units=[unit_id],
            filter_project=project.pk))
    assert not form.is_valid()
    assert (
        sorted(project_units.values_list("id", flat=True))
        == sorted(form.search().values_list("id", flat=True)))
    _test_batch(form, project_units)


@pytest.mark.django_db
def test_form_formtable_batch():
    form = DummySearchFormtableForm()
    project = form.fields["filter_project"].queryset.first()
    project_units = Unit.objects.filter(
        store__translation_project__project=project).order_by("id")

    # submit the form with page_no == 2
    form = DummySearchFormtableForm(
        data=dict(
            page_no=2,
            filter_project=project.pk))
    assert form.is_valid()
    assert (
        form.cleaned_data["page_no"]
        == form.batch().paginator.num_pages)
    _test_batch(form, project_units)

    # submit the form with page_no == max
    form = DummySearchFormtableForm(
        data=dict(
            page_no=form.batch().paginator.num_pages,
            filter_project=project.pk))
    assert form.is_valid()
    assert (
        form.cleaned_data["page_no"]
        == form.batch().paginator.num_pages)
    _test_batch(form, project_units)

    # submit the form with page_no == 2, per_page == 2
    form = DummySearchFormtableForm(
        data=dict(
            page_no=2,
            results_per_page=20,
            filter_project=project.pk))
    assert form.is_valid()
    assert (
        form.cleaned_data["page_no"]
        == form.batch().paginator.num_pages)
    _test_batch(form, project_units)

    # submit the form with page_no too high, form is valid
    # but page no is set to highest possible
    form = DummySearchFormtableForm(
        data=dict(
            page_no=form.batch().paginator.num_pages + 1,
            filter_project=project.pk))
    assert form.is_valid()
    assert (
        form.cleaned_data["page_no"]
        == form.batch().paginator.num_pages)
    _test_batch(form, project_units)

    # submit the form with bad results_per_page, form is valid and
    # results_per_page is set to a multiple of 10
    form = DummySearchFormtableForm(
        data=dict(
            results_per_page=23,
            filter_project=project.pk))
    assert form.is_valid()
    form.cleaned_data["results_per_page"] == 20
    assert (
        sorted(project_units.values_list("id", flat=True))
        == sorted(form.search().values_list("id", flat=True)))
    _test_batch(form, project_units)

    # submit the form with results_per_page set too high, form is valid and
    # results_per_page is set to default
    form = DummySearchFormtableForm(
        data=dict(
            results_per_page=200,
            filter_project=project.pk))
    assert form.is_valid()
    form.cleaned_data["results_per_page"] == 20
    assert (
        sorted(project_units.values_list("id", flat=True))
        == sorted(form.search().values_list("id", flat=True)))
    _test_batch(form, project_units)

    # submit the form with results_per_page set too high, form is valid and
    # results_per_page is set to default
    form = DummySearchFormtableForm(
        data=dict(
            results_per_page=200,
            filter_project=project.pk))
    assert form.is_valid()
    form.cleaned_data["results_per_page"] == 20
    assert (
        sorted(project_units.values_list("id", flat=True))
        == sorted(form.search().values_list("id", flat=True)))
    _test_batch(form, project_units)

    # submit the form with bad page_no, form is valid and page_no is default
    form = DummySearchFormtableForm(
        data=dict(
            page_no="NOT A PAGE NO",
            filter_project=project.pk))
    assert form.is_valid()
    assert form.cleaned_data["page_no"] == 1
    assert (
        sorted(project_units.values_list("id", flat=True))
        == sorted(form.search().values_list("id", flat=True)))
    _test_batch(form, project_units)


@pytest.mark.django_db
def test_form_formtable_no_comment():

    class DummyNoCommentFormtableForm(DummyFormtableForm):
        comment_field = None

    form = DummyNoCommentFormtableForm()
    assert "comment" not in form.fields
