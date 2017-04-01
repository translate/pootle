# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

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
