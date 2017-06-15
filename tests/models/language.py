# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from translate.lang.data import get_language_iso_fullname

from django.utils import translation

from pootle.core.delegate import site_languages
from pootle.i18n.gettext import tr_lang
from pootle_language.models import Language


@pytest.mark.django_db
def test_language_repr():
    language = Language.objects.first()
    assert (
        "<Language: %s - %s>" % (language.name, language.code)
        == repr(language))


@pytest.mark.django_db
def test_language_specialchars_uniqueness():
    language = Language.objects.first()
    language.specialchars = u"‌ æ ø å Æ Ø Å é è É È Ô ô"
    language.save()
    assert language.specialchars == u"‌ æøåÆØÅéèÉÈÔô"
    language.specialchars = u" Čč Ḍḍ Ɛɛ Ǧǧ Ɣɣ  Ḥḥ Ṣṣ ṬṬṭ Ẓẓ Ţţ Ṛṛ‌Ṛṛ‌"
    language.save()
    assert language.specialchars == u" ČčḌḍƐɛǦǧƔɣḤḥṢṣṬṭẒẓŢţṚṛ‌"


@pytest.mark.django_db
def test_language_display_name(english):
    english.fullname = ""
    english.save()

    # as fullname is not set - this should default to the pycountry name
    assert (
        english.name
        == get_language_iso_fullname(english.code))

    # lets give english a custom name in db
    english.fullname = "English (bristol twang)"
    english.save()

    # as we are translating to server lang, we use lang.fullname
    # and not the one from pycountry/iso translation
    assert (
        english.name
        == english.fullname)

    with translation.override("fr"):
        # now request lang has changed (and != server lang)
        # so we get the translated name
        assert (
            english.name
            == site_languages.get().capitalize(
                tr_lang(get_language_iso_fullname(english.code))))

    with translation.override("en-GB"):
        # as request lang is also a dialect of english
        # it uses the lang.fullname
        assert (
            english.name
            == english.fullname)
