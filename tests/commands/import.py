# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

import pytest

from django.core.management import call_command
from django.core.management.base import CommandError

from pytest_pootle.utils import get_translated_storefile


@pytest.mark.cmd
def test_import_user_nofile():
    """Missing 'file' positional argument."""
    with pytest.raises(CommandError) as e:
        call_command('import')
    assert "too few arguments" in str(e)


@pytest.mark.cmd
def test_import_user_non_existant_file():
    """No file on filesystem."""
    with pytest.raises(CommandError) as e:
        call_command('import', 'nofile.po')
    assert "No such file" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_import_emptyfile(capfd, tmpdir):
    """Load an empty PO file"""
    p = tmpdir.mkdir("sub").join("empty.po")
    p.write("")
    with pytest.raises(CommandError) as e:
        call_command('import', os.path.join(p.dirname, p.basename))
    assert "missing X-Pootle-Path header" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_import_onefile(capfd, tmpdir):
    """Load an one unit PO file"""
    from pootle_store.models import Store

    p = tmpdir.mkdir("sub").join("store0.po")
    store = Store.objects.get(pootle_path="/language0/project0/store0.po")
    p.write(str(get_translated_storefile(store)))
    call_command('import', os.path.join(p.dirname, p.basename))
    out, err = capfd.readouterr()
    assert "/language0/project0/store0.po" in err


@pytest.mark.cmd
@pytest.mark.django_db
def test_import_onefile_with_user(capfd, tmpdir, site_users):
    """Load an one unit PO file"""
    from pootle_store.models import Store

    user = site_users['user'].username
    p = tmpdir.mkdir("sub").join("store0.po")
    store = Store.objects.get(pootle_path="/language0/project0/store0.po")
    p.write(str(get_translated_storefile(store)))
    call_command('import', '--user=%s' % user,
                 os.path.join(p.dirname, p.basename))
    out, err = capfd.readouterr()
    assert user in out
    assert "[update]" in err
    assert "units in /language0/project0/store0.po" in err


@pytest.mark.cmd
@pytest.mark.django_db
def test_import_bad_user(tmpdir):
    from pootle_store.models import Store

    p = tmpdir.mkdir("sub").join("store0.po")
    store = Store.objects.get(pootle_path="/language0/project0/store0.po")
    p.write(str(get_translated_storefile(store)))
    with pytest.raises(CommandError) as e:
        call_command('import', '--user=not_a_user',
                     os.path.join(p.dirname, p.basename))
    assert "Unrecognised user: not_a_user" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_import_bad_pootlepath(tmpdir):
    """Bad X-Pootle-Path

    / missing before language0
    """
    from pootle_store.models import Store

    p = tmpdir.join("store0.po")
    store = Store.objects.get(pootle_path="/language0/project0/store0.po")
    p.write(str(
        get_translated_storefile(store,
                                 pootle_path="language0/project0/store0.po")))
    with pytest.raises(CommandError) as e:
        call_command('import', os.path.join(p.dirname, p.basename))
    assert "Missing Project/Language?" in str(e)
