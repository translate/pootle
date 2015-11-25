import os
import shutil

import pytest

from django.db import IntegrityError

from pootle_language.models import Language
from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject


@pytest.mark.django_db
def test_tp_create_fail(tutorial, english):

    # Trying to create a TP with no Project raises a RelatedObjectDoesNotExist
    # which can be caught with Project.DoesNotExist
    with pytest.raises(Project.DoesNotExist):
        TranslationProject.objects.create()

    # TP needs a lang set too...
    with pytest.raises(Language.DoesNotExist):
        TranslationProject.objects.create(project=tutorial)

    # There is already an english tutorial was automagically set up
    with pytest.raises(IntegrityError):
        TranslationProject.objects.create(project=tutorial, language=english)


@pytest.mark.django_db
def test_tp_create_no_files(tutorial, fish):
    # There are no files on disk so TP was not automagically created
    # and there are no templates loaded
    tp = TranslationProject.objects.create(project=tutorial, language=fish)
    assert list(tp.stores.all()) == []


def _test_tp_stores_match(tp1, tp2):
    # For testing tp creation from templates
    assert tp1.stores.count() == tp2.stores.count()
    tp1_stores = tp1.stores.all()
    tp2_stores = tp2.stores.all()

    for i, store1 in enumerate(tp1_stores):
        store2 = tp2_stores[i]
        assert store1.units == store2.units


@pytest.mark.django_db
def test_tp_create_templates(tutorial, klingon_vpw, templates):
    # As there is a tutorial template it will automatically create stores for
    # our new TP
    template_tp = TranslationProject.objects.get(
        language=templates, project=tutorial)
    tp = TranslationProject.objects.create(
        project=tutorial, language=klingon_vpw)
    assert tp.stores.count() == template_tp.stores.count()
    assert (
        [(s, t)
         for s, t
         in template_tp.stores.first().units.values_list("source_f",
                                                         "target_f")]
        == [(s, t)
            for s, t
            in tp.stores.first().units.values_list("source_f",
                                                   "target_f")])


@pytest.mark.django_db
def test_tp_create_with_files(tutorial, english, klingon, settings):
    # lets add some files by hand

    trans_dir = settings.POOTLE_TRANSLATION_DIRECTORY

    shutil.copytree(
        os.path.join(trans_dir, "tutorial/en"),
        os.path.join(trans_dir, "tutorial/kl"))

    TranslationProject.objects.create(project=tutorial, language=klingon)

    shutil.rmtree(os.path.join(trans_dir, "tutorial/kl"))
