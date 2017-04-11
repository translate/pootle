# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import pytest

from translate.filters.decorators import Category

from django.core.management import CommandError, call_command

from pootle_project.models import Project


@pytest.mark.cmd
@pytest.mark.django_db
def test_wrong_project_update():
    with pytest.raises(CommandError):
        call_command('project', 'update', 'wrong_project',
                     '--target-project=foo')


@pytest.mark.cmd
@pytest.mark.django_db
def test_project_clone_tp(capfd, po_directory, tutorial, admin):
    tp = tutorial.translationproject_set.get(language__code='language0')
    unit = tp.stores.first().units.first()
    unit.target_f = '%s\n%s' % (unit.source_f, unit.source_f)
    # set and mute critical check
    unit.save()
    unit.update_qualitychecks()
    check_id = unit.qualitycheck_set.filter(
        category=Category.CRITICAL).values_list('id', flat=True).first()
    unit.toggle_qualitycheck(check_id=check_id, false_positive=True, user=admin)
    call_command('project', 'clone', 'tutorial', '--target-project=zoo',
                 '--language=language0', '--target-language=language1')

    out, err = capfd.readouterr()
    assert (u'Translation project "/language0/tutorial/" has been cloned into '
            u'"/language1/zoo/"' in out)
    zoo = Project.objects.get(code='zoo')
    assert os.listdir(zoo.get_real_path())


@pytest.mark.cmd
@pytest.mark.django_db
def test_project_wrong_clone(project_foo):
    with pytest.raises(CommandError) as e:
        call_command('project', 'clone', 'project0', '--target-project=foo')

    assert 'Project <foo> already exists.' in e.value


@pytest.mark.cmd
@pytest.mark.django_db
def test_project_clone_tp_into_existing_project(capfd, project_foo):
    call_command('project', 'clone', 'project0', '--target-project=foo',
                 '--language=language0')
    out, err = capfd.readouterr()
    assert (u'Translation project "/language0/project0/" has been cloned into '
            u'"/language0/foo/"' in out)


@pytest.mark.cmd
@pytest.mark.django_db
def test_project_clone_with_wrong_disk_dir(project_foo):
    path = project_foo.get_real_path()
    project_foo.delete()
    with pytest.raises(CommandError) as e:
        call_command('project', 'clone', 'project0', '--target-project=foo')

    assert (u'Project <foo> code cannot be created from '
            u'project <project0> because "%s" directory already exists.' %
            path) in e.value


@pytest.mark.cmd
@pytest.mark.django_db
def test_project_remove(capfd, project_foo):
    foo = '%s' % project_foo
    call_command('project', 'remove', 'foo', '--force')

    out, err = capfd.readouterr()
    assert (u'Project "%s" has been deleted' % foo) in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_project_remove_tp(capfd, tp0):
    call_command('project', 'remove', 'project0', '--language=language0')

    out, err = capfd.readouterr()
    assert (u'Translation project "%s" has been deleted' % tp0) in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_project_clone_with_wrong_options():
    with pytest.raises(CommandError) as e:
        call_command('project', 'clone', 'project0', '--target-project=foo',
                     '--target-language=language1')
    assert ('You must set only one source language via --language option'
            in ('%s' % e.value))

    with pytest.raises(CommandError) as e:
        call_command('project', 'clone', 'project0')
    assert ('At least one of target-language and target-project is required.'
            in ('%s' % e.value))
