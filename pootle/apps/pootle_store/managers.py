# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db import models

from pootle.core.url_helpers import split_pootle_path
from pootle_app.models import Directory

from .constants import OBSOLETE


class SuggestionManager(models.Manager):

    def pending(self):
        return self.get_queryset().filter(state__name="pending")


class UnitManager(models.Manager):

    def live(self):
        """Filters non-obsolete units."""
        return self.filter(state__gt=OBSOLETE, store__obsolete=False)

    def get_for_user(self, user):
        """Filters units for a specific user.

        - Admins always get all non-obsolete units
        - Regular users only get units from enabled projects accessible
            to them.

        :param user: The user for whom units need to be retrieved for.
        :return: A filtered queryset with `Unit`s for `user`.
        """
        from pootle_project.models import Project

        if user.is_superuser:
            return self.live()

        user_projects = Project.accessible_by_user(user)
        filter_by = {
            "store__translation_project__project__disabled": False,
            "store__translation_project__project__code__in": user_projects
        }
        return self.live().filter(**filter_by)

    def get_translatable(self, user, project_code=None, language_code=None,
                         dir_path=None, filename=None):
        """Returns translatable units for a `user`, optionally filtered by their
        location within Pootle.

        :param user: The user who is accessing the units.
        :param project_code: A string for matching the code of a Project.
        :param language_code: A string for matching the code of a Language.
        :param dir_path: A string for matching the dir_path and descendants
           from the TP.
        :param filename: A string for matching the filename of Stores.
        """

        units_qs = self.get_for_user(user)

        if language_code:
            units_qs = units_qs.filter(
                store__translation_project__language__code=language_code)
        else:
            units_qs = units_qs.exclude(store__is_template=True)

        if project_code:
            units_qs = units_qs.filter(
                store__translation_project__project__code=project_code)

        if not (dir_path or filename):
            return units_qs

        tp_path = "/%s%s" % (
            dir_path or "",
            filename or "")
        if filename:
            return units_qs.filter(
                store__tp_path=tp_path)
        else:
            return units_qs.filter(
                store__tp_path__startswith=tp_path)


class StoreManager(models.Manager):

    def live(self):
        """Filters non-obsolete stores."""
        return self.filter(obsolete=False)

    def create(self, *args, **kwargs):
        if "filetype" not in kwargs:
            filetypes = kwargs["translation_project"].project.filetype_tool
            kwargs['filetype'] = filetypes.choose_filetype(kwargs["name"])
        if kwargs["translation_project"].is_template_project:
            kwargs["is_template"] = True
        kwargs["pootle_path"] = (
            "%s%s"
            % (kwargs["parent"].pootle_path, kwargs["name"]))
        kwargs["tp_path"] = (
            "%s%s"
            % (kwargs["parent"].tp_path, kwargs["name"]))
        return super(StoreManager, self).create(*args, **kwargs)

    def get_or_create(self, *args, **kwargs):
        store, created = super(StoreManager, self).get_or_create(*args, **kwargs)
        if not created:
            return store, created
        update = False
        if store.translation_project.is_template_project:
            store.is_template = True
            update = True
        if "filetype" not in kwargs:
            filetypes = store.translation_project.project.filetype_tool
            store.filetype = filetypes.choose_filetype(store.name)
            update = True
        if update:
            store.save()
        return store, created

    def create_by_path(self, pootle_path, project=None,
                       create_tp=True, create_directory=True, **kwargs):
        from pootle_language.models import Language
        from pootle_project.models import Project

        (lang_code, proj_code,
         dir_path, filename) = split_pootle_path(pootle_path)

        ext = filename.split(".")[-1]

        if project is None:
            project = Project.objects.get(code=proj_code)
        elif project.code != proj_code:
            raise ValueError(
                "Project must match pootle_path when provided")
        if ext not in project.filetype_tool.valid_extensions:
            raise ValueError(
                "'%s' is not a valid extension for this Project"
                % ext)
        if create_tp:
            tp, created = (
                project.translationproject_set.get_or_create(
                    language=Language.objects.get(code=lang_code)))
        elif create_directory or not dir_path:
            tp = project.translationproject_set.get(
                language__code=lang_code)
        if dir_path:
            if not create_directory:
                parent = Directory.objects.get(
                    pootle_path="/".join(
                        ["", lang_code, proj_code, dir_path]))
            else:
                parent = tp.directory
                for child in dir_path.strip("/").split("/"):
                    parent, created = Directory.objects.get_or_create(
                        tp=tp, name=child, parent=parent)
        else:
            parent = tp.directory

        store, created = self.get_or_create(
            name=filename, parent=parent, translation_project=tp, **kwargs)
        return store
