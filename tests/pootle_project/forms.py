# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_language.models import Language
from pootle_project.forms import TranslationProjectForm


@pytest.mark.django_db
def test_form_project_tp(tp0):
    form = TranslationProjectForm(
        instance=tp0,
        data=dict(
            project=tp0.project.pk,
            language=tp0.language.pk))
    assert form.is_valid()
    assert form.cleaned_data["project"] == tp0.project
    assert form.cleaned_data["language"] == tp0.language
    assert form.cleaned_data["fs_code"] == ""

    form = TranslationProjectForm(
        instance=tp0,
        data=dict(
            project=tp0.project.pk,
            language=tp0.language.pk,
            fs_code="foo"))
    assert form.is_valid()
    assert form.cleaned_data["fs_code"] == "foo"
    form.save()
    project = tp0.project
    del project.__dict__["config"]
    assert (
        tp0.project.config[
            "pootle.core.lang_mapping"]["foo"]
        == tp0.language.code)
    tp1 = project.translationproject_set.get(
        language__code="language1")
    form = TranslationProjectForm(
        instance=tp1,
        data=dict(
            project=tp1.project.pk,
            language=tp1.language.pk,
            fs_code="foo"))
    assert not form.is_valid()
    assert form.errors.keys() == ["fs_code"]
    form = TranslationProjectForm(
        instance=tp1,
        data=dict(
            project=tp1.project.pk,
            language=tp1.language.pk,
            fs_code=tp0.language.code))
    assert not form.is_valid()
    assert form.errors.keys() == ["fs_code"]
    new_language = Language.objects.create(code="foo")
    form = TranslationProjectForm(
        initial=dict(project=project.pk),
        data=dict(
            project=tp1.project.pk,
            language=new_language.pk))
    assert not form.is_valid()
    assert form.errors.keys() == ["language"]
    form = TranslationProjectForm(
        instance=tp0,
        data=dict(
            project=tp0.project.pk,
            language=tp0.language.pk,
            fs_code=""))
    assert form.is_valid()
    assert form.cleaned_data["fs_code"] == ""
    form.save()
    del project.__dict__["config"]
    assert (
        "foo" not in
        project.config[
            "pootle.core.lang_mapping"])
