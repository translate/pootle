# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pytest_pootle.factories import (LanguageDBFactory, ProjectDBFactory,
                                     TranslationProjectFactory)

from pootle_language.models import Language


@pytest.mark.django_db
def test_language_repr():
    language = Language.objects.first()
    assert (
        "<Language: %s>" % language.name
        == repr(language))


@pytest.mark.django_db
def test_language_only_in_disabled_proj_liveness(templates, project0,
                                                 templates_project0):
    project0.disabled = True
    project0.save()

    assert project0.disabled
    assert templates.translationproject_set.count() == 1
    assert templates not in Language.live.all()
    assert templates in Language.live.get_all_queryset()


@pytest.mark.django_db
def test_language_liveness():
    language = LanguageDBFactory()

    # Test unused language is not live.
    assert language.translationproject_set.count() == 0
    assert language not in Language.live.all()
    assert language not in Language.live.get_all_queryset()

    # Create obsolete TP.
    obsolete_tp = TranslationProjectFactory(
        language=language,
        project=ProjectDBFactory(source_language=language)
    )
    obsolete_tp.directory.makeobsolete()

    # Test language used only in obsolete TP is not live.
    assert obsolete_tp.directory.obsolete
    assert language.translationproject_set.count() == 1
    assert language not in Language.live.all()
    assert language not in Language.live.get_all_queryset()

    # Create TP for disabled project.
    disabled_project = ProjectDBFactory(source_language=language)
    disabled_project.disabled = True
    disabled_project.save()
    disabled_project_tp = TranslationProjectFactory(language=language,
                                                    project=disabled_project)

    # Test language used only in disabled project and obsolete TP is not live.
    assert disabled_project.disabled
    assert language.translationproject_set.count() == 2
    assert language not in Language.live.all()
    # But live for admins.
    assert language in Language.live.get_all_queryset()

    # Create regular TP.
    TranslationProjectFactory(
        language=language,
        project=ProjectDBFactory(source_language=language)
    )

    # Test language used in regular and obsolete TPs and in TP on disabled
    # project is live.
    assert language.translationproject_set.count() == 3
    assert language in Language.live.all()
    # But live for admins.
    assert language in Language.live.get_all_queryset()

    # Delete TP for disabled project.
    disabled_project_tp.delete()

    # Test language both in obsolete and regular TP is live.
    assert language.translationproject_set.count() == 2
    assert language in Language.live.all()
    assert language in Language.live.get_all_queryset()

    # Create again TP for disabled project and delete obsolete TP.
    # Delete obsolete TP.
    disabled_project_tp = TranslationProjectFactory(language=language,
                                                    project=disabled_project)
    obsolete_tp.delete()

    # Test language both in disabled project and regular TP is live.
    assert language.translationproject_set.count() == 2
    assert language in Language.live.all()
    assert language in Language.live.get_all_queryset()

    # Delete TP for disabled project.
    disabled_project_tp.delete()

    # Test templates language is live.
    assert language.translationproject_set.count() == 1
    assert language in Language.live.all()
    assert language in Language.live.get_all_queryset()
