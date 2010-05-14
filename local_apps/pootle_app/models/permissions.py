#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.db import models
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from pootle_app.lib.util import RelatedManager

def get_pootle_permission(codename):
    # The content type of our permission
    content_type = ContentType.objects.get(name='pootle', app_label='pootle_app')
    # Get the pootle view permission
    return Permission.objects.get(content_type=content_type, codename=codename)

def get_pootle_permissions(codenames=None):
    """gets the available rights and their localized names"""
    content_type = ContentType.objects.get(name='pootle', app_label='pootle_app')
    if codenames is not None:
        permissions = Permission.objects.filter(content_type=content_type, codename__in=codenames)
    else:
        permissions = Permission.objects.filter(content_type=content_type)
    return dict((permission.codename, permission) for permission in permissions)

def get_matching_permissions(profile, directory):
    permission_query = PermissionSet.objects.filter(directory__in=directory.trail(only_dirs=False)).order_by('-directory__pootle_path')
    if profile.user.is_authenticated():
        user_query = permission_query.filter(profile=profile)
        if user_query.count():
            return user_query[0].to_dict()
        else:
            return permission_query.filter(profile__user__username='default')[0].to_dict()
    else:
        return permission_query.filter(profile__user__usernae='nobody')[0].to_dict()

def check_profile_permission(profile, permission_codename, directory):
    """it checks if current user has the permission the perform C{permission_codename}"""
    if profile.user.is_superuser:
        return True
    permissions = get_matching_permissions(profile, directory)
    return permission_codename in permissions

def check_permission(permission_codename, request):
    """it checks if current user has the permission the perform C{permission_codename}"""
    if request.user.is_superuser:
        return True
    return permission_codename in request.permissions

class PermissionSet(models.Model):
    objects = RelatedManager()
    class Meta:
        unique_together = ('profile', 'directory')
        app_label = "pootle_app"

    profile                = models.ForeignKey('pootle_profile.PootleProfile', db_index=True)
    directory              = models.ForeignKey('pootle_app.Directory', db_index=True, related_name='permission_sets')
    positive_permissions   = models.ManyToManyField(Permission, db_index=True, related_name='permission_sets_positive')
    # negative permissions are no longer used, kept around to scheme
    # compatibility with older versions
    negative_permissions   = models.ManyToManyField(Permission, db_index=True, related_name='permission_sets_negative')

    def __unicode__(self):
        return "%s : %s" % (self.profile.user.username, self.directory.pootle_path)

    def to_dict(self):
        return dict((permission.codename, permission) for permission in self.positive_permissions.iterator())
