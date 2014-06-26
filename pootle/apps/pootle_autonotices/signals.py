#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
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


##### TranslationProject Events #####

def updated_against_template(sender, **kwargs):
    args = {
        'url': sender.get_absolute_url(),
        'sender': sender.fullname,
    }
    message = ('Updated <a href="%(url)s">%(sender)s</a> '
               'to latest template' % args)
    new_object(True, message, sender.directory)


def updated_from_version_control(sender, **kwargs):
    if sender.is_template_project:
        # Add template news to project instead of translation project.
        directory = sender.project.directory
    else:
        directory = sender.directory

    args = {
        'url': sender.get_absolute_url(),
        'sender': sender.fullname,
    }
    message = ('Updated <a href="%(url)s">%(sender)s</a> '
               'from version control' % args)
    new_object(True, message, directory)


def committed_to_version_control(sender, path_obj, user, success, **kwargs):
    args = {
        'user_url': user.get_absolute_url(),
        'user': get_profile(user),
        'path_obj_url': path_obj.get_absolute_url(),
        'path_obj': path_obj.pootle_path,
    }
    message = ('<a href="%(user_url)s">%(user)s</a> committed <a '
               'href="%(path_obj_url)s">%(path_obj)s</a> to version control' %
               args)

    total = path_obj.get_total_wordcount()
    translated = path_obj.get_translated_wordcount()
    fuzzy = path_obj.get_fuzzy_wordcount()
    message = stats_message_raw(message, total, translated, fuzzy)
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

    old_total = oldstats["total"]
    new_total = newstats["total"]
    old_translated = oldstats["translated"]
    new_translated = newstats["translated"]
    old_fuzzy = oldstats["fuzzy"]
    new_fuzzy = newstats["fuzzy"]
    message += stats_message_raw('Before upload', old_total, old_translated,
                                 old_fuzzy) + ' <br />'
    message += stats_message_raw('After upload', new_total, new_translated,
                                 new_fuzzy) + ' <br />'
    new_object(True, message, directory)
