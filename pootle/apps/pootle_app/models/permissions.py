#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
# Copyright 2014 Evernote Corporation
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
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.utils.encoding import iri_to_uri

from pootle.core.managers import RelatedManager


def get_permission_contenttype():
    content_type = ContentType.objects.filter(name='pootle',
                                              app_label='pootle_app',
                                              model="directory")[0]
    return content_type


def get_pootle_permission(codename):
    # The content type of our permission
    content_type = get_permission_contenttype()
    # Get the pootle view permission
    return Permission.objects.get(content_type=content_type, codename=codename)


def get_pootle_permissions(codenames=None):
    """Gets the available rights and their localized names."""
    content_type = get_permission_contenttype()

    if codenames is not None:
        permissions = Permission.objects.filter(content_type=content_type,
                                                codename__in=codenames)
    else:
        permissions = Permission.objects.filter(content_type=content_type)

    return dict((permission.codename, permission) for permission in permissions)


def get_permissions_by_username(username, directory):
    pootle_path = directory.pootle_path
    path_parts = filter(None, pootle_path.split('/'))
    key = iri_to_uri('Permissions:%s' % username)
    permissions_cache = cache.get(key, {})

    if pootle_path not in permissions_cache:
        try:
            permissionset = PermissionSet.objects.filter(
                directory__in=directory.trail(only_dirs=False),
                user__username=username).order_by("-directory__pootle_path")[0]
        except IndexError:
            permissionset = None

        if (len(path_parts) > 1 and path_parts[0] != 'projects' and
            (permissionset is None or
            len(filter(None, permissionset.directory.pootle_path.split('/'))) < 2)):
                # Active permission at language level or higher, check project
                # level permission
                try:
                    project_path = '/projects/%s/' % path_parts[1]
                    permissionset = PermissionSet.objects \
                            .get(directory__pootle_path=project_path,
                                 user__username=username)
                except PermissionSet.DoesNotExist:
                    pass

        if permissionset:
            permissions_cache[pootle_path] = permissionset.to_dict()
        else:
            permissions_cache[pootle_path] = None

        cache.set(key, permissions_cache, settings.OBJECT_CACHE_TIMEOUT)

    return permissions_cache[pootle_path]


def get_matching_permissions(user, directory, check_default=True):
    if user.is_authenticated():
        permissions = get_permissions_by_username(user.username,
                                                  directory)
        if permissions is not None:
            return permissions

        if not check_default:
            return {}

        permissions = get_permissions_by_username('default', directory)
        if permissions is not None:
            return permissions

    permissions = get_permissions_by_username('nobody', directory)

    return permissions


def check_user_permission(user, perm_code, directory, check_default=True):
    """Check if the current user has the permission to perform ``perm_code``."""
    if user.is_superuser:
        return True

    permissions = get_matching_permissions(user, directory, check_default)

    return ("administrate" in permissions or perm_code in permissions)


def check_permission(perm_code, request):
    """Check if the current user has `perm_code` permission."""
    if request.user.is_superuser:
        return True

    # `view` permissions are project-centric, and we must treat them
    # differently
    if perm_code == 'view':
        path_obj = None
        if hasattr(request, 'translation_project'):
            path_obj = request.translation_project
        elif hasattr(request, 'project'):
            path_obj = request.project

        if path_obj is None:
            return True  # Always allow to view language pages

        return path_obj.is_accessible_by(request.user)

    permissions = request.permissions

    return ("administrate" in permissions or perm_code in permissions)


class PermissionSet(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True)
    directory = models.ForeignKey(
        'pootle_app.Directory',
        db_index=True,
        related_name='permission_sets',
    )
    positive_permissions = models.ManyToManyField(
        Permission,
        db_index=True,
        related_name='permission_sets_positive',
    )
    negative_permissions = models.ManyToManyField(
        Permission,
        db_index=True,
        related_name='permission_sets_negative',
    )

    objects = RelatedManager()

    class Meta:
        unique_together = ('user', 'directory')
        app_label = "pootle_app"

    def __unicode__(self):
        return "%s : %s" % (self.user.username, self.directory.pootle_path)

    def to_dict(self):
        permissions_iterator = self.positive_permissions.iterator()
        return dict((perm.codename, perm) for perm in permissions_iterator)

    def save(self, *args, **kwargs):
        super(PermissionSet, self).save(*args, **kwargs)
        # FIXME: can we use `post_save` signals or invalidate caches in
        # model managers, please?
        username = self.user.username
        keys = [
            iri_to_uri('Permissions:%s' % username),
            iri_to_uri('projects:accessible:%s' % username),
        ]
        cache.delete_many(keys)

    def delete(self, *args, **kwargs):
        super(PermissionSet, self).delete(*args, **kwargs)
        # FIXME: can we use `post_delete` signals or invalidate caches in
        # model managers, please?
        username = self.user.username
        keys = [
            iri_to_uri('Permissions:%s' % username),
            iri_to_uri('projects:accessible:%s' % username),
        ]
        cache.delete_many(keys)
