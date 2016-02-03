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


@pytest.mark.cmd
@pytest.mark.django_db
def test_update_tmserver_nosetting(capfd, afrikaans_tutorial):
    """We need configured TM for anything to work"""
    with pytest.raises(CommandError) as e:
        call_command('update_tmserver')
    assert "POOTLE_TM_SERVER setting is missing." in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def __test_update_tmserver_noargs(capfd, afrikaans_tutorial, settings):
    """Load TM from the database"""

    from pootle_store.models import Unit

    units_qs = (
        Unit.objects
            .exclude(target_f__isnull=True)
            .exclude(target_f__exact=''))

    settings.POOTLE_TM_SERVER = {
        'local': {
            'ENGINE': 'pootle.core.search.backends.ElasticSearchBackend',
            'HOST': 'localhost',
            'PORT': 9200,
            'INDEX_NAME': 'translations',
        }
    }
    call_command('update_tmserver')
    out, err = capfd.readouterr()
    assert "Last indexed revision = -1" in out

    assert ("%d translations to index" % units_qs.count()) in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_update_tmserver_bad_tm(capfd, settings):
    """Non-existant TM in the server"""
    settings.POOTLE_TM_SERVER = {
        'local': {
            'ENGINE': 'pootle.core.search.backends.ElasticSearchBackend',
            'HOST': 'localhost',
            'PORT': 9200,
            'INDEX_NAME': 'translations',
        }
    }
    with pytest.raises(CommandError) as e:
        call_command('update_tmserver', '--tm=i_dont_exist')
    assert "Translation Memory 'i_dont_exist' is not defined" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_update_tmserver_files_no_displayname(capfd, settings, tmpdir):
    """File based TM needs a display-name"""
    settings.POOTLE_TM_SERVER = {
        'external': {
            'ENGINE': 'pootle.core.search.backends.ElasticSearchBackend',
            'HOST': 'localhost',
            'PORT': 9200,
            'INDEX_NAME': 'translations-external',
        }
    }
    with pytest.raises(CommandError) as e:
        call_command('update_tmserver', '--tm=external', 'fake_file.po')
    assert "--display-name" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_update_tmserver_files(capfd, settings, tmpdir):
    """Load TM from files"""
    settings.POOTLE_TM_SERVER = {
        'external': {
            'ENGINE': 'pootle.core.search.backends.ElasticSearchBackend',
            'HOST': 'localhost',
            'PORT': 9200,
            'INDEX_NAME': 'translations-external',
        }
    }
    p = tmpdir.mkdir("tmserver_files").join("tutorial.po")
    p.write("""msgid "rest"
msgstr "test"
           """)

    # First try without a --target-language (headers in above PO would sort
    # this out)
    with pytest.raises(CommandError) as e:
        call_command('update_tmserver', '--tm=external', '--display-name=Test',
                     os.path.join(p.dirname, p.basename))
    assert "Unable to determine target language" in str(e)

    # Now set the --target-language
    call_command('update_tmserver', '--tm=external', '--display-name=Test',
                 '--target-language=af', os.path.join(p.dirname, p.basename))
    out, err = capfd.readouterr()
    assert "1 translations to index" in out
