#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
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

"""Pootle version-specific upgrade actions."""

from __future__ import absolute_import
import logging
from django.utils.translation import ugettext_noop as _


def upgrade_to_25201():
    """New semantics for the `view` permission."""
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    from pootle_app.models import Directory
    from pootle_app.models.permissions import PermissionSet

    # Remove old `view` permission
    Permission.objects.filter(codename='view').delete()

    # Create new `view` permission
    pootle_content_type = ContentType.objects.get(
        app_label='pootle_app',
        model='directory',
    )
    view = Permission.objects.create(
        name=_(u'Can view a project'),
        content_type=pootle_content_type,
        codename='view',
    )

    # Attach `view` permission to the root directory for anonymous and
    # default users
    User = get_user_model()
    nobody = User.objects.get(username='nobody')
    default = User.objects.get(username='default')

    root = Directory.objects.root
    permission_set = PermissionSet.objects.get(
        user=nobody,
        directory=root,
    )
    permission_set.positive_permissions.add(view)

    permission_set = PermissionSet.objects.get(
        user=default,
        directory=root,
    )
    permission_set.positive_permissions.add(view)


def upgrade_to_25203():
    """Set `Submission` model's type to the new `SubmissionTypes.SYSTEM` for
    submissions performed by the `system` user.
    """
    from pootle_statistics.models import Submission, SubmissionTypes

    Submission.objects.filter(type=None, submitter__username="system") \
                      .update(type=SubmissionTypes.SYSTEM)


def upgrade_to_25205():
    """Synchronize latest submission data with the denormalized submission
    fields available in the :cls:`pootle_store.models.Unit` model.
    """
    from pootle_statistics.models import SubmissionFields
    from pootle_store.models import Unit

    logging.info('About to synchronize latest submission data.')

    rows = Unit.objects.filter(
        submission__field__in=[
            SubmissionFields.SOURCE,
            SubmissionFields.STATE,
            SubmissionFields.TARGET,
        ],
    ).select_related('submission__creation_time',
                     'submission__submitter') \
     .order_by('id', '-submission__creation_time') \
     .values('id', 'submission__creation_time', 'submission__submitter')

    saved_id = None
    for row in rows:
        unit_id = row['id']
        if saved_id is None or saved_id != unit_id:
            last_submitter = row['submission__submitter']
            last_submission_time = row['submission__creation_time']
            Unit.objects.filter(id=unit_id).update(
                submitted_by=last_submitter,
                submitted_on=last_submission_time,
            )
            saved_id = unit_id

    logging.info('Succesfully synchronized latest submission data.')


def upgrade_to_25206():
    """Set a correct build version for Translate Toolkit.

    Since Pootle 2.5.1 the upgrade for Translate Toolkit was using the Pootle
    build version. This fix is meant to save a working build version so
    future upgrades for Translate Toolkit are run.

    Note that this is Translate Toolkit fix is being run as an upgrade for
    Pootle because the Pootle upgrades are being run before the Translate
    Toolkit ones.
    """
    from . import save_build_version
    save_build_version('ttk', 12008)


def upgrade_to_25999():
    """
    Create the "view" and "hide permissions.
    """
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    content_type, created = ContentType.objects.\
                            get_or_create(app_label="pootle_app",
                                          model="directory")
    content_type.name = "pootle"
    content_type.save()

    logging.info("Updating 'view' permission")
    view_permission, created = Permission.objects.get_or_create(
        codename="view",
        content_type=content_type,
    )
    view_permission.name = _("Can access a project")
    view_permission.save()

    logging.info("Creating 'hide' permission")
    Permission.objects.get_or_create(
        name=_("Cannot access a project"),
        codename="hide",
        content_type=content_type,
    )
