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
def test_project_update(capfd, language0, project0, project_foo, admin):
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
    unit.target_f += '\n CHANGED'
    unit.save()
    unit.update_qualitychecks()
    check_id = unit.qualitycheck_set.filter(
        category=Category.CRITICAL).values_list('id', flat=True).first()
    unit.toggle_qualitycheck(check_id=check_id, false_positive=True, user=admin)

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
                 '--target-project=foo', '--target-language=language1')

    out, err = capfd.readouterr()
    assert (u'Translation project "/language0/project0/" has been moved into '
            u'"/language1/foo/"' in out)


@pytest.mark.cmd
@pytest.mark.django_db
def test_project_move_tp_within_project(capfd):
    call_command('project', 'remove', 'project0', '--language=language1')
    call_command('project', 'move', 'project0', '--language=language0',
                 '--target-language=language1')

    out, err = capfd.readouterr()
    assert (u'Translation project "/language0/project0/" has been moved into '
            u'"/language1/project0/"' in out)


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


@pytest.mark.cmd
@pytest.mark.django_db
def test_project_tp_move_to_wrong_language():
    with pytest.raises(CommandError) as e:
        call_command('project', 'move', 'project0', '--target-project=project1',
                     '--language=language0', '--target-language=language_foo')
    assert 'Language matching query does not exist' in ('%s' % e.value)


@pytest.mark.cmd
@pytest.mark.django_db
def test_project_tp_update(tp0, language1):
    from pootle_store.constants import UNTRANSLATED, TRANSLATED
    call_command('project', 'clone', 'project0', '--language=language0',
                 '--target-project=cloned_project',
                 '--target-language=language1')

    store = tp0.stores.first()
    unit = store.units.filter(state=UNTRANSLATED).first()
    unit.target_f = unit.source_f + ' TRANSLATION'
    unit.save()
    cloned_project = Project.objects.get(code='cloned_project')
    cloned_tp = cloned_project.translationproject_set.get(language=language1)
    store_path = store.pootle_path.replace('/language0/project0',
                                           '/language1/cloned_project')
    cloned_store = cloned_tp.stores.get(pootle_path=store_path)
    cloned_unit = cloned_store.units.get(unitid_hash=unit.unitid_hash)
    assert cloned_unit.state == UNTRANSLATED
    call_command('project', 'update', 'project0', '--language=language0',
                 '--target-project=cloned_project',
                 '--target-language=language1')
    assert cloned_store.units.get(id=cloned_unit.id).state == TRANSLATED
