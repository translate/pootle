# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.core.exceptions import ValidationError
from django.db import models

from pootle_language.models import Language
from pootle_project.models import Project
from pootle_store.models import Store


def validate_store_fs(**kwargs):
    """When creating or saving a StoreFS, validate that it has the necessary
    information.
    """
    store = kwargs.get("store")
    project = kwargs.get("project")
    pootle_path = kwargs.get("pootle_path")
    path = kwargs.get("path")

    # We must have a pootle_path somehow
    if not (store or pootle_path):
        raise ValidationError(
            "Either store or pootle_path must be set")

    # Lets see if there is a Store matching pootle_path
    if not store:
        try:
            store = Store.objects.get(pootle_path=pootle_path)
        except Store.DoesNotExist:
            pass

    if store:
        if not project:
            project = store.translation_project.project

        if not pootle_path:
            pootle_path = store.pootle_path

        # If store is set then pootle_path should match
        if store.pootle_path != pootle_path:
            raise ValidationError(
                "Store.pootle_path must match pootle_path: %s %s"
                % (pootle_path, store.pootle_path))

    # We must be able to calculate a pootle_path and path
    if not (pootle_path and path):
        raise ValidationError(
            "StoreFS must be created with at least a pootle_path and path")

    # If project is not set then get from the pootle_path
    try:
        path_project = Project.objects.get(code=pootle_path.split("/")[2])
    except (IndexError, Project.DoesNotExist):
        raise ValidationError("Unrecognised project in path: %s" % pootle_path)

    if not project:
        project = path_project
    elif project != path_project:
        raise ValidationError(
            "Path does not match project: %s %s"
            % (project, pootle_path))

    # Ensure language exists
    if not store:
        try:
            Language.objects.get(code=pootle_path.split("/")[1])
        except (IndexError, Language.DoesNotExist):
            raise ValidationError(
                "Unrecognised language in path: %s"
                % pootle_path)

    kwargs["project"] = project
    kwargs["store"] = store
    kwargs["pootle_path"] = pootle_path
    return kwargs


class StoreFSManager(models.Manager):

    def create(self, *args, **kwargs):
        kwargs = validate_store_fs(**kwargs)
        return super(StoreFSManager, self).create(*args, **kwargs)
