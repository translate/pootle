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

from pootle.core.delegate import revision


@pytest.mark.cmd
@pytest.mark.django_db
def test_export_noargs(capfd, export_dir, cd_export_dir):
    """Export whole site"""
    call_command('export')
    out, err = capfd.readouterr()
    assert 'Created project0-language0.zip' in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_export_project(capfd, export_dir, cd_export_dir):
    """Export a project"""
    call_command('export', '--project=project0')
    out, err = capfd.readouterr()
    assert 'project0.zip' in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_export_project_and_lang(capfd, export_dir, cd_export_dir):
    """Export a project TP"""
    call_command('export', '--project=project0', '--language=language0')
    out, err = capfd.readouterr()
    assert 'project0-language0.zip' in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_export_language(capfd, export_dir, cd_export_dir):
    """Export a language"""
    call_command('export', '--language=language0')
    out, err = capfd.readouterr()
    assert 'language0.zip' in out
    assert 'language1.zip' not in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_export_path(capfd, export_dir, cd_export_dir):
    """Export a path

    Testing variants of lang, TP, single PO file and whole site.
    """
    call_command('export', '--path=/language0')
    out, err = capfd.readouterr()
    assert 'language0.zip' in out
    assert 'language1.zip' not in out

    call_command('export', '--path=/language0/project0')
    out, err = capfd.readouterr()
    assert 'language0-project0.zip' in out

    call_command('export', '--path=/language0/project0/store0.po')
    out, err = capfd.readouterr()
    assert 'store0.po' in out

    call_command('export', '--path=/')
    out, err = capfd.readouterr()
    assert 'export.zip' in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_export_path_unknown():
    """Export an unknown path"""
    with pytest.raises(CommandError) as e:
        call_command('export', '--path=/af/unknown')
    assert "Could not find store matching '/af/unknown'" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_export_tmx_tp(capfd, tp0, media_test_dir):
    """Export a tp"""
    lang_code = tp0.language.code
    prj_code = tp0.project.code
    call_command('export', '--tmx', '--project=%s' % prj_code,
                 '--language=%s' % lang_code)
    out, err = capfd.readouterr()
    rev = revision.get(tp0.__class__)(tp0.directory).get(key="stats")
    filename = '%s.%s.%s.tmx.zip' % (
        tp0.project.code,
        tp0.language.code, rev[:10])
    assert os.path.join(lang_code, filename) in out

    call_command('export', '--tmx', '--project=%s' % prj_code,
                 '--language=%s' % lang_code)
    out, err = capfd.readouterr()
    assert 'Translation project (%s) has not been changed' % tp0 in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_export_tmx_with_wrong_options(capfd):
    with pytest.raises(CommandError) as e:
        call_command('export', '--tmx', '--path=/language0/project0/store0.po')
    assert "--path: not allowed with argument --tmx" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_export_tmx_tp_rotate(capfd, tp0, project1, media_test_dir):
    """Export a tp"""
    lang_code = tp0.language.code
    prj_code = tp0.project.code
    tp1 = project1.translationproject_set.get(language__code=lang_code)
    export_dir = os.path.join(media_test_dir, 'offline_tm')
    call_command('export', '--tmx', '--project=%s' % prj_code,
                 '--language=%s' % lang_code)
    out, err = capfd.readouterr()

    def get_filename(tp):
        rev = revision.get(tp.__class__)(tp.directory).get(key="stats")
        filename = '%s.%s.%s.tmx.zip' % (
            tp.project.code,
            tp.language.code, rev[:10])
        return os.path.join(lang_code, filename)

    filename_1 = get_filename(tp0)
    assert '%s" has been saved' % filename_1 in out
    assert os.path.exists(os.path.join(export_dir, filename_1))

    unit = tp0.stores.first().units.first()
    unit.target_f = unit.target_f + ' CHANGED'
    unit.save()
    call_command('export', '--tmx', '--project=%s' % prj_code,
                 '--language=%s' % lang_code)
    out, err = capfd.readouterr()

    filename_2 = get_filename(tp0)
    assert '%s" has been saved' % filename_2 in out
    assert os.path.exists(os.path.join(export_dir, filename_2))
    assert os.path.exists(os.path.join(export_dir, filename_1))

    unit = tp0.stores.first().units.first()
    unit.target_f = unit.target_f + ' CHANGED'
    unit.save()
    call_command('export', '--tmx', '--rotate', '--project=%s' % prj_code,
                 '--language=%s' % lang_code)
    out, err = capfd.readouterr()

    filename_3 = get_filename(tp0)
    assert '%s" has been saved' % filename_3 in out
    assert '%s" has been removed' % filename_1 in out
    assert '%s" has been removed' % filename_2 not in out

    assert not os.path.exists(os.path.join(export_dir, filename_1))
    assert os.path.exists(os.path.join(export_dir, filename_2))
    assert os.path.exists(os.path.join(export_dir, filename_3))

    call_command('export', '--tmx', '--rotate',
                 '--project=%s' % tp1.project.code,
                 '--language=%s' % tp1.language.code)
    out, err = capfd.readouterr()
    filename_for_tp1 = get_filename(tp1)
    assert '%s" has been saved' % filename_for_tp1 in out
    assert os.path.exists(os.path.join(export_dir, filename_for_tp1))
    assert os.path.exists(os.path.join(export_dir, filename_2))
    assert os.path.exists(os.path.join(export_dir, filename_3))
