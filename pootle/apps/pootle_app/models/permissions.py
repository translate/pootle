# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .directory import Directory


def get_permission_contenttype():
    content_type = ContentType.objects.get_for_model(Directory)
    return content_type


def get_pootle_permission(codename):
    # The content type of our permission
    content_type = get_permission_contenttype()
    # Get the pootle view permission
    return Permission.objects.get(content_type=content_type, codename=codename)


def get_permissions_by_user(user, directory):
    pootle_path = directory.pootle_path
    path_parts = filter(None, pootle_path.split('/'))
    try:
        permissionset = user.permissionset_set.select_related("directory").filter(
            directory__in=directory.trail(
                only_dirs=False)).order_by('-directory__pootle_path')[0]
    except IndexError:
        permissionset = None

    check_project_permissions = (
        (len(path_parts) > 1
         and path_parts[0] != 'projects'
         and (permissionset is None
              or len(
                  filter(
                      None,
                      permissionset.directory.pootle_path.split('/'))) < 2)))

    if check_project_permissions:
        # Active permission at language level or higher, check project
        # level permission
        try:
            project_path = '/projects/%s/' % path_parts[1]
            permissionset = user.permissionset_set.select_related("directory").get(
                directory__pootle_path=project_path)
        except PermissionSet.DoesNotExist:
            pass

    if permissionset:
        return permissionset.to_dict()
    else:
        return None


def get_matching_permissions(user, directory, check_default=True):
    User = get_user_model()

    if user.is_authenticated:
        permissions = get_permissions_by_user(user, directory)
        if permissions is not None:
            return permissions

        if not check_default:
            return {}

        permissions = get_permissions_by_user(
            User.objects.get_default_user(), directory)
        if permissions is not None:
            return permissions

    permissions = get_permissions_by_user(
        User.objects.get_nobody_user(), directory)

    return permissions


def check_user_permission(user, permission_codename, directory,
                          check_default=True):
    """Checks if the current user has the permission to perform
    ``permission_codename``.
    """
    if user.is_superuser:
        return True

    permissions = get_matching_permissions(user, directory, check_default)

    return ("administrate" in permissions or
            permission_codename in permissions)


def check_permission(permission_codename, request):
    """Checks if the current user has `permission_codename`
    permissions.
    """
    if request.user.is_superuser:
        return True

    # `view` permissions are project-centric, and we must treat them
    # differently
    if permission_codename == 'view':
        path_obj = None
        if hasattr(request, 'translation_project'):
            path_obj = request.translation_project
        elif hasattr(request, 'project'):
            path_obj = request.project

        if path_obj is None:
            return True  # Always allow to view language pages

        return path_obj.is_accessible_by(request.user)

    return ("administrate" in request.permissions or
            permission_codename in request.permissions)


class PermissionSet(models.Model):

    class Meta(object):
        unique_together = ('user', 'directory')
        app_label = "pootle_app"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_index=False,
        on_delete=models.CASCADE)
    directory = models.ForeignKey('pootle_app.Directory', db_index=True,
                                  related_name='permission_sets',
                                  on_delete=models.CASCADE)
    positive_permissions = models.ManyToManyField(
        Permission, db_index=True, related_name='permission_sets_positive')
    negative_permissions = models.ManyToManyField(
        Permission, db_index=True, related_name='permission_sets_negative')

    def __unicode__(self):
        return "%s : %s" % (self.user.username,
                            self.directory.pootle_path)

    def to_dict(self):
        permissions_iterator = self.positive_permissions.iterator()
        return dict((perm.codename, perm) for perm in permissions_iterator)
