#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""A set of signal handlers for generating automatic notifications on system
events."""

from pootle_app.models import Directory
from pootle_notifications.models import Notice


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
