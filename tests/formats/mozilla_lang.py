# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pytest_pootle.factories import StoreDBFactory

from pootle_format.models import Format
from pootle_store.constants import FUZZY, TRANSLATED
from pootle_store.models import Unit


@pytest.mark.django_db
def test_mozlang_update(tp0):
    mozlang = Format.objects.get(name="lang")
    tp0.project.filetypes.add(mozlang)

    foo_lang = StoreDBFactory(
        name="foo.lang",
        filetype=mozlang,
        parent=tp0.directory,
        translation_project=tp0)

    store0 = tp0.stores.get(name="store0.po")

    # deserialize as source
    foo_lang.update(store0.deserialize(store0.serialize()))

    # get serialized lang store
    serialized = foo_lang.serialize()

    # mark a translated unit as fuzzy
    translated = foo_lang.units.filter(state=TRANSLATED).first()
    translated.state = FUZZY
    translated.save()

    # source is translated
    foo_lang.update(foo_lang.deserialize(serialized))
    # unit is set back to TRANSLATED
    translated = Unit.objects.get(pk=translated.pk)
    assert translated.state == TRANSLATED

    translated = foo_lang.units.filter(state=TRANSLATED).first()
    translated.state = FUZZY
    translated.save()

    # set target == "" > untranslated
    ttk = foo_lang.deserialize(serialized)
    ttkunit = ttk.findid(translated.getid())
    ttkunit.target = ""
    foo_lang.update(ttk)
    # unit stays FUZZY
    translated = Unit.objects.get(pk=translated.pk)
    assert translated.state == FUZZY


@pytest.mark.django_db
def test_mozlang_sync(tp0):
    mozlang = Format.objects.get(name="lang")
    tp0.project.filetypes.add(mozlang)

    foo_lang = StoreDBFactory(
        name="foo.lang",
        filetype=mozlang,
        parent=tp0.directory,
        translation_project=tp0)

    store0 = tp0.stores.get(name="store0.po")

    # deserialize as source
    foo_lang.update(store0.deserialize(store0.serialize()))

    # mark the unit as fuzzy
    unit = foo_lang.units.filter(state=TRANSLATED).first()
    unit.markfuzzy()
    unit.save()

    ttk = foo_lang.deserialize(foo_lang.serialize())
    ttk_unit = ttk.findid(unit.getid())
    assert not ttk_unit.istranslated()


@pytest.mark.django_db
def test_mozlang_sync_to_file(project0_nongnu, store0, tp0):
    mozlang = Format.objects.get(name="lang")
    tp0.project.filetypes.add(mozlang)

    foo_lang = StoreDBFactory(
        name="foo.lang",
        filetype=mozlang,
        parent=tp0.directory,
        translation_project=tp0)

    store0 = tp0.stores.get(name="store0.po")

    # deserialize as source
    foo_lang.update(store0.deserialize(store0.serialize()))
    foo_lang.sync()

    header = "## SOME HEADER"

    # add some headers...
    with open(foo_lang.file.path, "wb") as f:
        content = (
            "%s\n\n\n%s"
            % (header, str(foo_lang)))
        f.write(content)

    unit = foo_lang.units.first()
    unit.target = "NEW TARGET FOO"
    unit.save()
    foo_lang.sync()

    with open(foo_lang.file.path) as f:
        new_file_contents = f.read()

    assert new_file_contents.startswith(header)
    assert "NEW TARGET FOO" in new_file_contents
