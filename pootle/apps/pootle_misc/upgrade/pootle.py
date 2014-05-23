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

import logging


def upgrade_to_21060():
    """Post-upgrade actions for upgrades to 21060."""
    from pootle_misc.util import deletefromcache
    from pootle_store.models import OBSOLETE
    from pootle_translationproject.models import TranslationProject

    logging.info('Flushing cached stats')

    for tp in TranslationProject.objects.filter(stores__unit__state=OBSOLETE) \
                                        .distinct().iterator():
        deletefromcache(tp, ["getquickstats", "getcompletestats", "get_mtime",
                             "has_suggestions"])


def upgrade_to_22000():
    """Post-upgrade actions for upgrades to 22000."""
    from django.core.cache import cache
    from django.utils.encoding import iri_to_uri

    from pootle_store.models import Store

    # In previous versions, we cached the sync times, so let's see if we can
    # recover some.
    for store in Store.objects.iterator():
        key = iri_to_uri("%s:sync" % store.pootle_path)
        last_sync = cache.get(key)
        if last_sync:
            store.sync_time = last_sync
            store.save()


def upgrade_to_25100():
    """Post-upgrade actions for upgrades to 25100."""
    from pootle_app.models import Directory

    # Create the new directory used for goals.
    Directory.objects.root.get_or_make_subdir('goals')


def upgrade_to_25200():
    """Post-upgrade actions for upgrades to 25200."""
    from pootle.core.initdb import create_local_tm

    logging.info('About to create the local translation memory.')
    create_local_tm()
    logging.info('Succesfully created the local translation memory.')


def upgrade_to_25201():
    """New semantics for the `view` permission."""
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    from django.utils.translation import ugettext_noop as _

    from pootle_app.models import Directory
    from pootle_app.models.permissions import PermissionSet
    from pootle_profile.models import PootleProfile

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
    nobody = PootleProfile.objects.get(user__username='nobody')
    default = PootleProfile.objects.get(user__username='default')

    root = Directory.objects.root
    permission_set = PermissionSet.objects.get(
        profile=nobody,
        directory=root,
    )
    permission_set.positive_permissions.add(view)

    permission_set = PermissionSet.objects.get(
        profile=default,
        directory=root,
    )
    permission_set.positive_permissions.add(view)


def upgrade_to_25202():
    from pootle.core.initdb import create_system_user

    create_system_user()


def upgrade_to_25203():
    """Set `Submission` model's type to the new `SubmissionTypes.SYSTEM` for
    submissions performed by the `system` user.
    """
    from pootle_statistics.models import Submission, SubmissionTypes

    Submission.objects.filter(
        type=None,
        submitter__user__username='system',
    ).update(
        type=SubmissionTypes.SYSTEM,
    )


def upgrade_to_25204():
    """Copy site title and description stored using djblets to new models."""
    from pootle.core.initdb import create_default_pootle_site
    from pootle_app.models.pootle_site import (get_legacy_site_description,
                                               get_legacy_site_title)

    # Copy the Pootle site data.
    create_default_pootle_site(
        get_legacy_site_title(),
        get_legacy_site_description()
    )


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
