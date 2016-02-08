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

from pootle.core.models import Revision


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
def test_import_emptyfile(capfd, afrikaans_tutorial, tmpdir):
    """Load an empty PO file"""
    p = tmpdir.mkdir("sub").join("empty.po")
    p.write("")
    with pytest.raises(CommandError) as e:
        call_command('import', os.path.join(p.dirname, p.basename))
    assert "missing X-Pootle-Path header" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_import_onefile(capfd, afrikaans_tutorial, tmpdir):
    """Load an one unit PO file"""
    p = tmpdir.mkdir("sub").join("tutorial.po")
    p.write("""msgid ""
msgstr ""
"X-Pootle-Path: /af/tutorial/tutorial.po\\n"
"X-Pootle-Revision: %s\\n"

msgid "rest"
msgstr "test"
           """ % (Revision.get() + 1))
    call_command('import', os.path.join(p.dirname, p.basename))
    out, err = capfd.readouterr()
    assert "[update]" in err
    assert "obsoleted 3" in err
    assert "added 1" in err
    assert "/af/tutorial/tutorial.po" in err


@pytest.mark.cmd
@pytest.mark.django_db
def test_import_onefile_with_user(capfd, afrikaans_tutorial, tmpdir, member):
    """Load an one unit PO file"""
    p = tmpdir.mkdir("sub").join("tutorial.po")
    p.write("""msgid ""
msgstr ""
"X-Pootle-Path: /af/tutorial/tutorial.po\\n"
"X-Pootle-Revision: %s\\n"

msgid "rest"
msgstr "test"
           """ % (Revision.get() + 1))
    call_command('import', '--user=member', os.path.join(p.dirname, p.basename))
    out, err = capfd.readouterr()
    assert "[update]" in err
    assert "obsoleted 3" in err
    assert "added 1" in err
    assert "/af/tutorial/tutorial.po" in err
    with pytest.raises(CommandError) as e:
        call_command('import', '--user=not_a_user',
                     os.path.join(p.dirname, p.basename))
    assert "Unrecognised user: not_a_user" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_import_bad_pootlepath(afrikaans_tutorial, tmpdir):
    """Bad X-Pootle-Path

    / missing before af
    """
    p = tmpdir.mkdir("sub").join("tutorial.po")
    p.write("""msgid ""
msgstr ""
"X-Pootle-Path: af/tutorial/tutorial.po\\n"
"X-Pootle-Revision: 12\\n"

msgid "rest"
msgstr "test"
           """)
    with pytest.raises(CommandError) as e:
        call_command('import', os.path.join(p.dirname, p.basename))
    assert "Missing Project/Language?" in str(e)
