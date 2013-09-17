#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
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


def upgrade_to_20030():
    """Post-upgrade actions for upgrades to 20030."""
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    logging.info('Fixing permissions table')

    criteria = {
        'app_label': "pootle_app",
        'model': "directory",
    }
    contenttype, created = ContentType.objects.get_or_create(**criteria)

    for permission in Permission.objects.filter(content_type__name='pootle') \
                                        .iterator():
        permission.content_type = contenttype
        permission.save()

    contenttype.name = 'pootle'
    contenttype.save()


def import_suggestions(store):
    try:
        logging.debug(u'Importing suggestions for %s (if any)',
                      store.real_path)
        store.import_pending()

        try:
            count = store.has_suggestions()
        except:
            count = store.get_suggestion_count()

        if count:
            logging.debug(u'Imported suggestions (%d) from %s',
                          store.real_path, count)
    except:
        logging.debug(u'Failed to import suggestions from %s', store.real_path)


def parse_store(store):
    try:
        logging.debug(u'Importing strings from %s', store.real_path)
        store.require_units()
        count = store.getquickstats()['total']
        logging.debug(u'Imported strings (%d) from %s', store.real_path, count)
    except:
        logging.debug(u'Failed to import strings from %s', store.real_path)


def upgrade_to_21000():
    """Post-upgrade actions for upgrades to 21000."""
    from pootle_app.models import Directory
    from pootle_project.models import Project
    from pootle_store.models import Store

    logging.info('Creating project directories')

    Directory.objects.root.get_or_make_subdir('projects')

    for project in Project.objects.iterator():
        # Saving should force project to update it's directory property.
        try:
            project.save()
        except Exception as e:
            logging.info(u'Something broke while upgrading %s:\n%s', project,
                         e)

    logging.info('Associating stores with translation projects')

    for store in Store.objects.iterator():
        try:
            store.translation_project = store.parent.translation_project
            store.save()
        except Exception as e:
            logging.info(u'Something broke while upgrading %s:\n%s',
                         store.pootle_path, e)

    logging.info('Importing translations into the database. This can take a '
                 'while.')

    for store in Store.objects.iterator():
        try:
            parse_store(store)
            import_suggestions(store)
        except Exception as e:
            logging.info(u'Something broke while parsing %s:\n%s', store, e)

    logging.info(u'All translations are now imported')


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
