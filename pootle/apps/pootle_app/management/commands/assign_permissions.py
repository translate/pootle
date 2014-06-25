#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <http://www.gnu.org/licenses/>.

import logging
import os
from optparse import make_option

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand, CommandError

from pootle_app.models.permissions import PermissionSet, get_pootle_permission
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
            make_option('--project', dest='project_code',
                        help='Project to assign permissions to. Use with '
                             '--language to specify a translation project.'),
            make_option('--language', dest='language_code',
                        help='Language to assign permissions to. Use with '
                             '--project to specify a translation project.'),
            make_option('--user', dest='username', metavar='USERNAME',
                        help='Username to assign permissions to.'),
            make_option('--permissions', dest='permissions',
                        help='Comma separated list of permissions codenames '
                             'to assign. Like view,suggest,translate or just'
                             'translate'),
    )
    help = ("Assign permissions to a user in a project, language or "
            "translation project.")

    def handle(self, *args, **options):
        """Assign permissions to a user in a project, language or translation
        project.
        """
        project_code = options.get('project_code', None)
        language_code = options.get('language_code', None)
        username = options.get('username', None)
        permissions = options.get('permissions', None)

        # Make sure all the required parameters are provided.
        if username is None:
            raise CommandError("A username must be provided.")

        if permissions is None:
            raise CommandError("A permissions list must be provided.")

        if project_code is None and language_code is None:
            raise CommandError("Either a project code or a language code must "
                               "be provided.")

        # Get the object we are assigning permissions for. This object can be a
        # translation project, a language or a project. This checks if it
        # exists.
        if project_code is not None and language_code is not None:
            try:
                criteria = {
                    'project__code': project_code,
                    'language__code': language_code,
                }
                perms_for = TranslationProject.objects.get(**criteria)
            except TranslationProject.DoesNotExist:
                raise CommandError("Translation project for project '%s' and "
                                   "language '%s' doesn't exist." %
                                   (project_code, language_code))
        elif project_code is not None:
            try:
                perms_for = Project.objects.get(code=project_code)
            except Project.DoesNotExist:
                raise CommandError("Project '%s' does not exist." %
                                   project_code)
        elif language_code is not None:
            try:
                perms_for = Language.objects.get(code=language_code)
            except Language.DoesNotExist:
                raise CommandError("Language '%s' does not exist." %
                                   language_code)

        # Get the User for the specified username. This checks if it exists.
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError("User '%s' does not exist." % username)

        # Get all the specified permissions. This checks if they exist.
        permission_list = permissions.split(",")
        perms_dict = {}

        for permission in permission_list:
            try:
                perms_dict[permission] = get_pootle_permission(permission)
            except Permission.DoesNotExist:
                raise CommandError("Permission with code '%s' doesn't exist." %
                                   permission)

        # Assign the permissions to the user.
        params = {
            'user': user,
            'directory': perms_for.directory,
        }
        permission_set, created = PermissionSet.objects.get_or_create(**params)

        if created:
            # If the user doesn't yet have any permission for this object, just
            # apply all the permissions.
            permission_set.positive_permissions = perms_dict.values()
            permission_set.save()
        else:
            # If the user already has some permissions for this object.
            has_perms = permission_set.positive_permissions.all()
            has_perms_list = "\n\t".join([perm.codename for perm in has_perms])
            logging.info("The user already has the permissions:\n\t%s",
                         has_perms_list)

            # Get the permissions not yet applied.
            missing_perms = [permission for permission in perms_dict.values()
                                        if permission not in has_perms]
            missing_perms_list = "\n\t".join([perm.codename for perm in
                                              missing_perms])
            logging.info("About to apply the missing permissions:\n\t%s",
                         missing_perms_list)

            # Apply the missing permissions.
            for missing in missing_perms:
                permission_set.positive_permissions.add(missing)

        # Nofify success in permissions assignment.
        if project_code is not None and language_code is not None:
            logging.info("Sucessfully applied the permissions to user '%s' in "
                         "translation project for project '%s' and language "
                         "'%s'.", username, project_code, language_code)
        elif project_code is not None:
            logging.info("Sucessfully applied the permissions to user '%s' in "
                         "project '%s'.", username, project_code)
        elif language_code is not None:
            logging.info("Sucessfully applied the permissions to user '%s' in "
                         "language '%s'.", username, language_code)
