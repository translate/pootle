#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

"""A set of signal handlers for generating automatic notifications on system
events."""

import logging

from pootle_app.models import Directory
from pootle_misc.stats import stats_message_raw
from pootle_notifications.models import Notice
from pootle_profile.models import get_profile
from pootle_store.models import Unit


##### Model Events #####

def new_object(created, message, parent):
    if created:
        notice = Notice(directory=parent, message=message)
        notice.save()


def new_language(sender, instance, created=False, raw=False, **kwargs):
    if raw:
        return

    args = {
        'url': instance.get_absolute_url(),
        'language': instance.fullname,
    }
    message = 'New language <a href="%(url)s">%(language)s</a> created.' % args
    new_object(created, message, instance.directory.parent)


def new_project(sender, instance, created=False, raw=False, **kwargs):
    if raw:
        return

    args = {
        'url': instance.get_absolute_url(),
        'project': instance.fullname,
    }
    message = 'New project <a href="%(url)s">%(project)s</a> created.' % args
    new_object(created, message, parent=Directory.objects.root)


def new_user(sender, instance, created=False, raw=False, **kwargs):
    if raw:
        return

    # New user needs to be wrapped in a try block because it might be called
    # before the rest of the models are loaded when first installing Pootle.

    try:
        args = {
            'url': instance.get_profile().get_absolute_url(),
            'user': instance.get_profile(),
        }
        message = 'New user <a href="%(url)s">%(user)s</a> registered.' % args
        new_object(created, message, parent=Directory.objects.root)
    except:
        pass


def new_translationproject(sender, instance, created=False, raw=False,
                           **kwargs):
    if raw:
        return

    args = {
        'tp_url': instance.get_absolute_url(),
        'project_url': instance.project.get_absolute_url(),
        'project': instance.project.fullname,
        'language_url': instance.language.get_absolute_url(),
        'language': instance.language.fullname,
    }

    message = ('New project <a href="%(tp_url)s">%(project)s</a> added to '
               'language <a href="%(language_url)s">%(language)s</a>.' % args)
    new_object(created, message, instance.language.directory)

    message = ('New language <a href="%(tp_url)s">%(language)s</a> added to '
               'project <a href="%(project_url)s">%(project)s</a>.' % args)
    new_object(created, message, instance.project.directory)


def unit_updated(sender, instance, raw=False, **kwargs):
    if raw:
        return

    if instance.id is not None and instance.istranslated():
        dbcopy = Unit.objects.get(id=instance.id)
        if dbcopy.istranslated():
            # Unit state didn't change, let's quit.
            return

        store = instance.store
        stats = store.getquickstats()

        if stats['total'] - stats['translated'] == 1:
            # By the end of this we will be 100%.
            translation_project = store.translation_project
            directory = translation_project.directory
            args = {
                'url': store.get_absolute_url(),
                'store': store.name,
            }
            message = ('<a href="%(url)s">%(store)s</a> fully translated</a>'
                       '<br />' % args)
            quickstats = translation_project.getquickstats()
            quickstats['translated'] += 1

            if dbcopy.isfuzzy():
                quickstats['fuzzy'] -= 1

            message += stats_message_raw("Project now at", quickstats)
            new_object(True, message, directory)


##### TranslationProject Events #####

def updated_against_template(sender, oldstats, newstats, **kwargs):
    if oldstats == newstats:
        # Nothing changed, no need to report.
        return

    args = {
        'url': sender.get_absolute_url(),
        'sender': sender.fullname,
    }
    message = ('Updated <a href="%(url)s">%(sender)s</a> to latest template'
               '<br />' % args)
    message += stats_message_raw("Before update", oldstats) + " <br />"
    message += stats_message_raw("After update", newstats) + " <br />"
    new_object(True, message, sender.directory)


def updated_from_version_control(sender, oldstats, remotestats, newstats,
                                 **kwargs):
    if sender.is_template_project:
        # Add template news to project instead of translation project.
        directory = sender.project.directory
    else:
        directory = sender.directory

    if oldstats == newstats:
        # Nothing changed, no need to report.
        return

    args = {
        'url': sender.get_absolute_url(),
        'sender': sender.fullname,
    }
    message = ('Updated <a href="%(url)s">%(sender)s</a> from version control'
               '<br />' % args)
    message += stats_message_raw("Before update", oldstats) + " <br />"

    if not remotestats == newstats:
        message += stats_message_raw("Remote copy", remotestats) + " <br />"

    message += stats_message_raw("After update", newstats)
    new_object(True, message, directory)


def committed_to_version_control(sender, path_obj, stats, user, success,
                                 **kwargs):
    args = {
        'user_url': user.get_absolute_url(),
        'user': get_profile(user),
        'path_obj_url': path_obj.get_absolute_url(),
        'path_obj': path_obj.pootle_path,
    }
    message = ('<a href="%(user_url)s">%(user)s</a> committed <a '
               'href="%(path_obj_url)s">%(path_obj)s</a> to version control' %
               args)
    message = stats_message_raw(message, stats)
    new_object(success, message, sender.directory)


def file_uploaded(sender, oldstats, user, newstats, archive, **kwargs):
    if sender.is_template_project:
        # Add template news to project instead of translation project.
        directory = sender.project.directory
    else:
        directory = sender.directory

    if oldstats == newstats:
        logging.debug("file uploaded but stats didn't change")
        return

    args = {
        'user_url': get_profile(user).get_absolute_url(),
        'user': get_profile(user),
        'sender_url': sender.get_absolute_url(),
        'sender': sender.fullname,
    }
    if archive:
        message = ('<a href="%(user_url)s">%(user)s</a> uploaded an archive '
                   'to <a href="%(sender_url)s">%(sender)s</a> <br />' % args)
    else:
        message = ('<a href="%(user_url)s">%(user)s</a> uploaded a file to '
                   '<a href="%(sender_url)s">%(sender)s</a> <br />' % args)

    message += stats_message_raw('Before upload', oldstats) + ' <br />'
    message += stats_message_raw('After upload', newstats) + ' <br />'
    new_object(True, message, directory)
