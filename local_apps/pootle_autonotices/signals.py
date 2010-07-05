#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""A set of singal handlers for generating automatic notifications on system
events."""

import logging

from pootle_notifications.models import Notice
from pootle_app.models import Directory
from pootle_profile.models import get_profile

##### Model Events #####

def new_object(created, message, parent):
    if created:
        notice = Notice(directory=parent, message=message)
        notice.save()

def new_language(sender, instance, created=False, **kwargs):
    message = 'New language <a href="%s">%s</a> created.' % (instance.get_absolute_url(), instance.fullname)
    new_object(created, message, instance.directory.parent)

def new_project(sender, instance, created=False, **kwargs):
    message = 'New project <a href="%s">%s</a> created.' % (instance.get_absolute_url(), instance.fullname)
    new_object(created, message, parent=Directory.objects.root)

def new_user(sender, instance, created=False, **kwargs):
    # new user needs to be wrapped in a try block because it might be
    # called before the rest of the models are loaded when first
    # installing Pootle

    try:
        message = 'New user <a href="%s">%s</a> registered.' % (instance.get_profile().get_absolute_url(), instance.username)
        new_object(created, message, parent=Directory.objects.root)
    except:
        pass

def new_translationproject(sender, instance, created=False, **kwargs):
    message = 'New project <a href="%s">%s</a> added to language <a href="%s">%s</a>.' % (
        instance.get_absolute_url(), instance.project.fullname,
        instance.language.get_absolute_url(), instance.language.fullname)
    new_object(created, message, instance.language.directory)
    message = 'New language <a href="%s">%s</a> added to project <a href="%s">%s</a>.' % (
        instance.get_absolute_url(), instance.language.fullname,
        instance.project.get_absolute_url(), instance.project.fullname)
    new_object(created, message, instance.project.directory)

def unit_updated(sender, instance, **kwargs):
    if instance.id is not None:
        store = instance.store
        stats = store.getquickstats()
        if stats['total'] - stats['translated'] == 1 and instance.istranslated():
            # by the end of this we will be 100%
            translation_project = store.translation_project
            directory = translation_project.directory
            message = '<a href="%s">%s</a> fully translated</a> <br />' % (store.get_absolute_url(), store.name)
            message += stats_message("Project now at", translation_project.getquickstats())
            new_object(True, message, directory)

##### TranslationProject Events #####

from pootle_translationproject.models import stats_message

def updated_from_template(sender, oldstats, newstats, **kwargs):
    if oldstats == newstats:
        # nothing changed, no need to report
        return
    message = 'Updated <a href="%s">%s</a> to latest template <br />' % (sender.get_absolute_url(), sender.fullname)
    message += stats_message("Before update", oldstats) + " <br />"
    message += stats_message("After update", newstats) + " <br />"
    new_object(True, message, sender.directory)

def updated_from_version_control(sender, oldstats, remotestats, newstats, **kwargs):
    if sender.is_template_project:
        # add template news to project instead of translation project
        directory = sender.project.directory
    else:
        directory = sender.directory

    if oldstats == newstats:
        # nothing changed, no need to report
        return

    message = 'Updated <a href="%s">%s</a> from version control <br />' % (sender.get_absolute_url(), sender.fullname)
    message += stats_message("Before update", oldstats) + " <br />"
    if not remotestats == newstats:
        message += stats_message("Remote copy", remotestats) + " <br />"
    message += stats_message("After update", newstats)
    new_object(True, message, directory)

def committed_to_version_control(sender, store, stats, user, success, **kwargs):
    message = '<a href="%s">%s</a> committed <a href="%s">%s</a> to version control' % (
        user.get_absolute_url(), user.username,
        store.get_absolute_url(), store.pootle_path)
    message = stats_message(message, stats)
    new_object(success, message, sender.directory)

def file_uploaded(sender, oldstats, user, newstats, archive, **kwargs):
    if sender.is_template_project:
        # add template news to project instead of translation project
        directory = sender.project.directory
    else:
        directory = sender.directory

    if oldstats == newstats:
        logging.debug("file uploaded but stats didn't change")
        return

    if archive:
        message = '<a href="%s">%s</a> uploaded an archive to <a href="%s">%s</a> <br />' % (
            get_profile(user).get_absolute_url(), user.username,
            sender.get_absolute_url(), sender.fullname)
    else:
        message = '<a href="%s">%s</a> uploaded a file to <a href="%s">%s</a> <br />' % (
            get_profile(user).get_absolute_url(), user.username,
            sender.get_absolute_url(), sender.fullname)

    message += stats_message('Before upload', oldstats) + ' <br />'
    message += stats_message('After upload', newstats) + ' <br />'
    new_object(True, message, directory)


##### Profile Events #####

def user_joined_project(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == 'post_add' and not reverse:
        for project in instance.projects.filter(pk__in=pk_set).iterator():
            message = 'user <a href="%s">%s</a> joined project <a href="%s">%s</a>' % (
                instance.get_absolute_url(), instance.user.username,
                project.get_absolute_url(), project.fullname)
            new_object(True, message, project.directory)

def user_joined_language(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == 'post_add' and not reverse:
        for project in instance.languages.filter(pk__in=pk_set).iterator():
            message = 'user <a href="%s">%s</a> joined language <a href="%s">%s</a>' % (
                instance.get_absolute_url(), instance.user.username,
                project.get_absolute_url(), project.fullname)
            new_object(True, message, project.directory)

