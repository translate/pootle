# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.management import CommandError, call_command

from pootle.core.delegate import tp_tool
from pootle_project.models import Project
from pootle_store.models import Store


@pytest.mark.cmd
@pytest.mark.django_db
def test_wrong_project_update():
    with pytest.raises(CommandError):
        call_command('project', 'update', 'wrong_project',
                     '--target-project=foo')


@pytest.mark.cmd
@pytest.mark.django_db
def test_project_update(capfd, language0, project0, project_foo):
    from pytest_pootle.factories import StoreDBFactory

    call_command('project', 'update', 'project0',
                 '--target-project=foo', '--language=language0')
    out, err = capfd.readouterr()

    assert "Translation project (/language0/foo) is missing" in err
    assert Store.objects.filter(
        translation_project__project=project_foo).count() == 0

    tp = project0.translationproject_set.get(language=language0)
    tptool = tp_tool.get(Project)(project0)
    cloned_tp = tptool.clone(tp, language0, project=project_foo)

    store = tp.stores.first()
    unit = store.units.first()
    unit.target_f += ' CHANGED'
    unit.save()

    new_store = StoreDBFactory(translation_project=tp)

    call_command('project', 'update', '--translations',
                 'project0', '--target-project=foo')

    cloned_store = cloned_tp.stores.get(
        pootle_path=store.pootle_path.replace('project0', 'foo'))
    cloned_unit = cloned_store.units.get(source_hash=unit.source_hash)
    assert cloned_unit.target_f == unit.target_f

    with pytest.raises(Store.DoesNotExist):
        cloned_tp.stores.get(
            pootle_path=new_store.pootle_path.replace('project0', 'foo'))

    call_command('project', 'update', 'project0',
                 '--target-project=foo')

    new_cloned_store = cloned_tp.stores.get(
        pootle_path=new_store.pootle_path.replace('project0', 'foo'))

    assert new_cloned_store


@pytest.mark.cmd
@pytest.mark.django_db
def test_project_clone(capfd, language0, project_foo):
    # fill foo project
    project_foo.translationproject_set.create(language=language0)
    call_command('project', 'update', 'project0', '--target-project=foo')
    call_command('project', 'clone', 'foo', '--target-project=zoo',
                 '--language=language0')

    out, err = capfd.readouterr()
    assert (u'Translation project "/language0/foo/" has been cloned into '
            u'"/language0/zoo/"' in out)


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
def test_project_move(capfd, language0, project_foo):
    # fill foo project
    project_foo.translationproject_set.create(language=language0)
    call_command('project', 'update', 'project0', '--target-project=foo')
    call_command('project', 'move', 'foo', '--target-project=woo')

    out, err = capfd.readouterr()
    assert (u'Translation project "/language0/foo/" has been moved into '
            u'"/language0/woo/"' in out)


@pytest.mark.cmd
@pytest.mark.django_db
def test_project_move_tp(capfd):
    call_command('project', 'move', 'project0', '--language=language0',
                 '--target-project=foo')

    out, err = capfd.readouterr()
    assert (u'Translation project "/language0/project0/" has been moved into '
            u'"/language0/foo/"' in out)


@pytest.mark.cmd
@pytest.mark.django_db
def test_project_remove(capfd, project_foo):
    foo = '%s' % project_foo
    call_command('project', 'remove', 'foo')

    out, err = capfd.readouterr()
    assert (u'Project "%s" has been deleted' % foo) in out
