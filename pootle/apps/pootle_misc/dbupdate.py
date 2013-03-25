#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2012 Zuza Software Foundation
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

"""Automatic database update code used when upgrading to a new Pootle version.

When adding new fields in models, take into account the following:

    - Only use ``null=True`` for non-string fields such as integers,
      booleans and dates
    - If ``null=True`` is not set, then you need to set a default value
      for the field you are adding.
"""

import logging

from django.core.management import call_command

from pootle_app.models import Directory
from pootle_language.models import Language
from pootle_misc.util import deletefromcache
from pootle_project.models import Project
from pootle_store.models import Store, QualityCheck, CHECKED, PARSED
from pootle_store.util import OBSOLETE
from pootle_translationproject.models import TranslationProject


def flush_quality_checks():
    """Reverts stores to unchecked state.

    If a store has false positives marked, quality checks will be updated
    keeping false postivies intact."""
    for store in Store.objects.filter(state=CHECKED).iterator():
        store_checks = QualityCheck.objects.filter(unit__store=store)
        false_positives = store_checks.filter(false_positive=True).count()

        if false_positives:
            logging.debug("%s has false positives, updating quality checks",
                          store.pootle_path)

            for unit in store.units.iterator():
                unit.update_qualitychecks(keep_false_positives=True)
        else:
            logging.debug("%s has no false positives, deleting checks",
                          store.pootle_path)
            store_checks.delete()
            store.state = PARSED
            store.save()


def save_toolkit_version(build=None):
    from pootle_misc import siteconfig
    if not build:
        from translate.__version__ import build

    config = siteconfig.load_site_config()
    config.set('TT_BUILDVERSION', build)
    config.save()

    logging.info("Database now at Toolkit build %d" % build)


def save_pootle_version(build=None):
    from pootle_misc import siteconfig
    if not build:
        from pootle.__version__ import build

    config = siteconfig.load_site_config()
    config.set('BUILDVERSION', build)
    config.save()

    logging.info("Database now at Pootle build %d" % build)


def syncdb():
    logging.info("Creating missing database tables")

    call_command('syncdb', interactive=False)


def update_permissions_20030():
    logging.info("Fixing permissions table")

    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    contenttype, created = ContentType.objects \
                                      .get_or_create(app_label="pootle_app",
                                                     model="directory")

    for permission in Permission.objects.filter(content_type__name='pootle') \
                                        .iterator():
        permission.content_type = contenttype
        permission.save()

    contenttype.name = 'pootle'
    contenttype.save()

    save_pootle_version(20030)


def update_tables_21000():
    logging.info("Updating existing database tables")

    from south.db import db

    table_name = Store._meta.db_table
    field = Store._meta.get_field('state')
    db.add_column(table_name, field.name, field)
    db.create_index(table_name, (field.name,))

    field = Store._meta.get_field('translation_project')
    field.null = True
    db.add_column(table_name, field.name, field)
    db.create_index(table_name, (field.name + '_id',))

    table_name = Project._meta.db_table
    field = Project._meta.get_field('directory')
    field.null = True
    db.add_column(table_name, field.name, field)

    field = Project._meta.get_field('source_language')
    try:
        en = Language.objects.get(code='en')
    except Language.DoesNotExist:
        # We can't allow translation project detection to kick in yet so let's
        # create en manually
        en = Language(code='en', fullname='English', nplurals=2,
                      pluralequation="(n != 1)")
        en.directory = Directory.objects.root.get_or_make_subdir(en.code)
        en.save_base(raw=True)
    field.default = en.id
    db.add_column(table_name, field.name, field)
    db.create_index(table_name, (field.name + '_id',))
    # We shouldn't do save_pootle_version(21000) yet - more to do below


def update_stats_21060():
    logging.info('Flushing cached stats')

    for tp in TranslationProject.objects.filter(stores__unit__state=OBSOLETE) \
                                        .distinct().iterator():
        deletefromcache(tp, ["getquickstats", "getcompletestats",
                             "get_mtime", "has_suggestions"])

    # There's no need to save the schema version here as it will already be
    # saved by :func:`update_tables_22000`


def update_ts_tt_12008():
    logging.info('Reparsing Qt ts')

    for store in Store.objects \
                      .filter(state__gt=PARSED,
                              translation_project__project__localfiletype='ts',
                              file__iendswith='.ts').iterator():
        store.sync(update_translation=True)
        store.update(update_structure=True, update_translation=True,
                     conservative=False)

    save_toolkit_version(12008)


def update_tables_22000(flush_checks):
    logging.info("Updating existing database tables")

    from south.db import db

    # For the sake of South bug 313, we set the default for these fields here:
    # See http://south.aeracode.org/ticket/313
    from pootle_store.models import Suggestion
    table_name = Suggestion._meta.db_table
    field = Suggestion._meta.get_field('translator_comment_f')
    field.default = u''
    db.add_column(table_name, field.name, field)

    table_name = Language._meta.db_table
    field = Language._meta.get_field('description')
    field.default = u''
    db.add_column(table_name, field.name, field)

    field = Language._meta.get_field('description_html')
    field.default = u''
    db.add_column(table_name, field.name, field)

    table_name = TranslationProject._meta.db_table
    field = TranslationProject._meta.get_field('description')
    field.default = u''
    db.add_column(table_name, field.name, field)

    field = TranslationProject._meta.get_field('description_html')
    field.default = u''
    db.add_column(table_name, field.name, field)

    table_name = Project._meta.db_table
    field = Project._meta.get_field('report_target')
    field.default = u''
    db.add_column(table_name, field.name, field)

    field = Project._meta.get_field('description_html')
    field.default = u''
    db.add_column(table_name, field.name, field)

    table_name = QualityCheck._meta.db_table
    field = QualityCheck._meta.get_field('category')
    db.add_column(table_name, field.name, field)
    # Delete all 'hassuggestion' failures, since we don't actually use them
    # See bug 2412.
    QualityCheck.objects.filter(name="hassuggestion").delete()

    from pootle_statistics.models import Submission
    table_name = Submission._meta.db_table
    for field_name in ('unit', 'field', 'type', 'old_value', 'new_value'):
        field = Submission._meta.get_field(field_name)
        db.add_column(table_name, field.name, field)

    from pootle_store.models import Unit
    table_name = Unit._meta.db_table
    for field_name in ('submitted_by', 'submitted_on', 'commented_by',
                       'commented_on'):
        field = Unit._meta.get_field(field_name)
        db.add_column(table_name, field.name, field)

    from pootle_store.models import Store
    table_name = Store._meta.db_table
    field = Store._meta.get_field('sync_time')
    db.add_column(table_name, field.name, field)
    # In previous versions, we cached the sync times, so let's see if we can
    # recover some
    from django.core.cache import cache
    from django.utils.encoding import iri_to_uri
    for store in Store.objects.iterator():
        key = iri_to_uri("%s:sync" % store.pootle_path)
        last_sync = cache.get(key)
        if last_sync:
            store.sync_time = last_sync
            store.save()

    if flush_checks:
        logging.info("Fixing quality checks")
        flush_quality_checks()

    save_pootle_version(22000)


def update_toolkit_version():
    logging.info("New Translate Toolkit version, flushing quality checks")

    flush_quality_checks()
    save_toolkit_version()


def import_suggestions(store):
    try:
        logging.info(u"Importing suggestions for %s (if any)",
                     store.real_path)
        store.import_pending()

        try:
            count = store.has_suggestions()
        except:
            count = store.get_suggestion_count()

        if count:
            logging.info(u"Imported suggestions (%d) from %s",
                         store.real_path, count)
    except:
        logging.info(u"Failed to import suggestions from %s",
                     store.real_path)


def parse_store(store):
    try:
        logging.info(u"Importing strings from %s", store.real_path)
        store.require_units()
        count = store.getquickstats()['total']
        logging.info(u"Imported strings (%d) from %s",
                     store.real_path, count)
    except:
        logging.info(u"Failed to import strings from %s", store.real_path)


def staggered_update(db_buildversion, tt_buildversion, tt_version_changed):
    """Update pootle database, while displaying a progress report for each
    step."""
    needs_toolkit_upgrade = (tt_version_changed and
                             db_buildversion >= 21040)

    ############## version specific updates ############

    if db_buildversion < 20030:
        update_permissions_20030()

    if db_buildversion < 21000:
        try:
            update_tables_21000()
        except Exception, e:
            logging.warning(u"Something broke while upgrading database "
                            u"tables:\n%s", e)
            #TODO: should we continue?

        logging.info("Creating project directories")
        Directory.objects.root.get_or_make_subdir('projects')
        for project in Project.objects.iterator():
            # saving should force project to update it's directory property
            try:
                project.save()
            except Exception, e:
                logging.warning(u"Something broke while upgrading %s:\n%s",
                                project, e)

        logging.info("Associating stores with translation projects")
        for store in Store.objects.iterator():
            try:
                store.translation_project = store.parent.translation_project
                store.save()
            except Exception, e:
                logging.warning(u"Something broke while upgrading %s:\n%s",
                                store.pootle_path, e)

    # Build missing tables
    try:
        syncdb()
    except Exception, e:
        logging.warning(u"Something broke while creating new database tables:"
                        u"\n%s", e)

    if db_buildversion < 21000:
        logging.info(u"Importing translations into the database. This can "
                     u"take a while")
        for store in Store.objects.iterator():
            try:
                parse_store(store)
                import_suggestions(store)
            except Exception, e:
                logging.warning(u"Something broke while parsing %s:\n%s",
                                store, e)

        logging.info(u"All translations are now imported")
        save_pootle_version(21000)

    if db_buildversion < 22000:
        flush_checks = not needs_toolkit_upgrade
        update_tables_22000(flush_checks)

    # Since :func:`update_stats_21060` works with the :cls:`TranslationProject`
    # model, this has to go after upgrading the DB tables, otherwise the model
    # and DB table definitions don't match.
    if db_buildversion < 21060:
        update_stats_21060()

    if tt_buildversion < 12008:
        update_ts_tt_12008()

    if needs_toolkit_upgrade:
        # Let's clear stale quality checks data. We can only do that safely if
        # the db schema is already up to date.
        update_toolkit_version()
    elif tt_version_changed:
        # only need to update the toolkit version, not do the upgrade
        save_toolkit_version()

    logging.info(u"Calculating translation statistics, this will take "
                 u"a few minutes")

    # First time to visit the front page all stats for projects and
    # languages will be calculated which can take forever. Since users
    # don't like webpages that take forever let's precalculate the
    # stats here
    for language in Language.objects.iterator():
        logging.info(u"Language %s is %d%% complete", language.name,
                     language.translated_percentage())

    for project in Project.objects.iterator():
        logging.info(u"Project %s is %d%% complete", project.fullname,
                     project.translated_percentage())

    logging.info(u"Done calculating statistics")
