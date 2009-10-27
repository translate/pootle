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

"""Set of singal handlers for generating automatic notifications on system events"""



from pootle_notifications.models import Notice
from pootle_app.models import Directory
from pootle_misc.baseurl import l

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
    message = 'New user <a href="%s">%s</a> registered.' % (l('/accounts/%s/' % instance.username), instance.username)
    new_object(created, message, parent=Directory.objects.root)

def new_translationproject(sender, instance, created=False, **kwargs):
    message = 'New project <a href="%s">%s</a> added to language <a href="%s">%s</a>.' % (
        instance.get_absolute_url(), instance.project.fullname,
        instance.language.get_absolute_url(), instance.language.fullname)
    new_object(created, message, instance.directory.parent)


##### TranslationProject Events #####

from pootle_app.models.translation_project import stats_message

def updated_from_template(sender, oldstats, newstats, **kwargs):
    if oldstats == newstats:
        # nothing changed, no need to report
        return
    message = "Updated files to latest template<br/>\n"
    message += stats_message("Before update", oldstats) + "<br/>\n"
    message += stats_message("After update", newstats) + "<br/>\n"
    new_object(True, message, sender.directory)
    
def updated_from_version_control(sender, oldstats, remotestats, newstats, **kwargs):
    if oldstats == newstats:
        # nothing changed, no need to report
        return
    
    message = "Updated files from version control<br/>\n"
    message += stats_message("Before update", oldstats) + "<br/>\n"
    if not remotestats == newstats:
        message +=stats_message("Remote copy", remotestats) + "<br/>\n"
    message += stats_message("After update", newstats)
    new_object(True, message, sender.directory)

def committed_to_version_control(sender, store, stats, user, success, **kwargs):
    message = '<a href="%s">%s</a> committed <a href="%s">%s</a> to version control' % (
        l('/accounts/%s/' % user.username), user.username,
        store.get_absolute_url(), store.name)
    message = stats_message(message, stats)
    new_object(success, message, sender.directory)

##### Store events #####

def unit_updated(sender, oldstats, newstats, **kwargs):
    if oldstats == newstats:
        return
    
    if newstats['translatedsourcewords'] == newstats['totalsourcewords']:
        # find parent translation project
        directory = sender.parent
        while not directory.is_translationproject() and not directory == Directory.objects.root:
            directory = directory.parent
        
        message = '<a href="%s">%s</a> fully translated</a><br/>' % (sender.get_absolute_url(), sender.name)
        message += stats_message("Project now at", directory.getquickstats())
        new_object(True, message, directory)

