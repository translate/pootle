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
import sys

from django.core.management import call_command

from pootle.i18n.gettext import ungettext, ugettext as _
from pootle_app.models import Directory
from pootle_language.models import Language
from pootle_misc.dbinit import (stats_start, stats_language, stats_project,
                                stats_end)
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


def header(db_buildversion):
    text = """
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE html  PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
    <html>
    <head>
    <title>%(title)s</title>
    <meta content="text/html; charset=utf-8" http-equiv="content-type" />
    <style type="text/css">
    body
    {
        background-color: #ffffff;
        color: #000000;
        font-family: Georgia, serif;
        margin: 40px auto;
        width: 740px;
    }
    h1
    {
        font-size: 185%%;
    }
    ul
    {
        list-style-type: square;
    }
    .error
    {
        background-color: inherit;
        color: #d54e21;
        font-weight: bold;
    }
    </style>
    </head>
    <body>
    <h1>%(title)s</h1>
    <p class="error">%(msg)s</p>
    """ % {
        'title': _('Pootle: Update'),
        'msg': _('Database tables are currently at build version %d. '
                 'Pootle will now update the database.', db_buildversion)
    }

    return text


def syncdb():
    text = u"""
    <p>%s</p>
    """ % _('Creating missing database tables...')
    logging.info("Creating missing database tables")

    call_command('syncdb', interactive=False)

    return text


def update_permissions_20030():
    text = """
    <p>%s</p>
    """ % _('Fixing permission table...')
    logging.info("Fixing permission table")

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

    return text


def update_tables_21000():
    text = u"""
    <p>%s</p>
    """ % _('Updating existing database tables...')
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
    return text


def update_stats_21060():
    text = """
    <p>%s</p>
    """ %_('Removing potentially incorrect cached stats, will be '
           'recalculated...')
    logging.info('Flushing cached stats')

    for tp in TranslationProject.objects.filter(stores__unit__state=OBSOLETE) \
                                        .distinct().iterator():
        deletefromcache(tp, ["getquickstats", "getcompletestats",
                             "get_mtime", "has_suggestions"])

    # There's no need to save the schema version here as it will already be
    # saved by :func:`update_tables_22000`
    return text


def update_ts_tt_12008():
    text = """
    <p>%s</p>
    """ %_('Reparsing Qt ts files...')
    logging.info('Reparsing Qt ts')

    for store in Store.objects \
                      .filter(state__gt=PARSED,
                              translation_project__project__localfiletype='ts',
                              file__iendswith='.ts').iterator():
        store.sync(update_translation=True)
        store.update(update_structure=True, update_translation=True,
                     conservative=False)

    save_toolkit_version(12008)

    return text


def update_tables_22000(flush_checks):
    text = u"""
    <p>%s</p>
    """ % _('Updating existing database tables...')
    logging.info("Updating existing database tables")

    from south.db import db

    # For the sake of South bug 313, we set the default for these fields here:
    # See http://south.aeracode.org/ticket/313
    from pootle_store.models import Suggestion
    table_name = Suggestion._meta.db_table
    field = Suggestion._meta.get_field('translator_comment_f')
    field.default = u''
    db.add_column(table_name, field.name, field)

    from pootle_language.models import Language
    table_name = Language._meta.db_table
    field = Language._meta.get_field('description')
    field.default = u''
    db.add_column(table_name, field.name, field)

    field = Language._meta.get_field('description_html')
    field.default = u''
    db.add_column(table_name, field.name, field)

    from pootle_translationproject.models import TranslationProject
    table_name = TranslationProject._meta.db_table
    field = TranslationProject._meta.get_field('description')
    field.default = u''
    db.add_column(table_name, field.name, field)

    field = TranslationProject._meta.get_field('description_html')
    field.default = u''
    db.add_column(table_name, field.name, field)

    from pootle_project.models import Project
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
        text += """
        <p>%s</p>
        """ % _('Removing quality checks, will be recalculated on demand...')
        logging.info("Fixing quality checks")
        flush_quality_checks()

    save_pootle_version(22000)

    return text


def update_toolkit_version():
    text = """
    <p>%s</p>
    """ % _('Removing quality checks, will be recalculated on demand...')
    logging.info("New Translate Toolkit version, flushing quality checks")

    flush_quality_checks()
    save_toolkit_version()

    return text


def parse_start():
    text = u"""
    <p>%s</p>
    <ul>
    """ % _('Pootle will now import all the translations into the database. '
            'It could take a long time.')

    return text


def import_suggestions(store):
    try:
        logging.info(u"Importing suggestions for %s if any.", store.real_path)
        store.import_pending()

        try:
            count = store.has_suggestions()
        except:
            count = store.get_suggestion_count()

        if count:
            text = u"""
            <li>%s</li>
            """ % ungettext('Imported %(count)d suggestion from %(store)s',
                            'Imported %(count)d suggestions from %(store)s',
                            count, {'count': count, 'store': store.pootle_path})
        else:
            text = ""
    except:
        text = u"""
        <li class="error">%s</li>
        """ % _('Failed to import suggestions from %s', store.pootle_path)

    return text


def parse_store(store):
    try:
        logging.info(u"Importing units from %s", store.real_path)
        store.require_units()
        count = store.getquickstats()['total']
        text = u"""
        <li>%s</li>
        """ % ungettext('Imported %(count)d unit from %(store)s',
                        'Imported %(count)d units from %(store)s',
                        count, {'count': count, 'store': store.pootle_path})
    except:
        text = u"""
        <li class="error">%s</li>
        """ % _('Failed to import units from %s', store.pootle_path)

    return text


def parse_end():
    text = u"""
    </ul>
    <p>%s</p>
    """ % _('All translations are now imported.')

    return text


def footer():
    text = """
    <p>%(endmsg)s</p>
    <div><script>setTimeout("location.reload()", 10000)</script></div>
    </body></html>
    """ % {'endmsg': _('Pootle initialized the database. You will be '
                       'redirected to the front page in 10 seconds.')}

    return text


def staggered_update(db_buildversion, tt_buildversion):
    """Update pootle database, while displaying a progress report for each
    step."""
    # django's syncdb command prints progress reports to stdout, but
    # mod_wsgi doesn't like stdout, so we reroute to stderr
    stdout = sys.stdout
    sys.stdout = sys.stderr

    yield header(db_buildversion)

    # sys.maxint is set in siteconfig middleware if Toolkit is unchanged.
    # Otherwise, Toolkit build version changed.
    needs_toolkit_upgrade = (tt_buildversion != sys.maxint and
                             db_buildversion >= 21040)

    ############## version specific updates ############

    if db_buildversion < 20030:
        yield update_permissions_20030()

    if db_buildversion < 21000:
        try:
            yield update_tables_21000()
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
                store.translation_project = store.parent.get_translationproject()
                store.save()
            except Exception, e:
                logging.warning(u"Something broke while upgrading %s:\n%s",
                                store.pootle_path, e)

    # Build missing tables
    try:
        yield syncdb()
    except Exception, e:
        logging.warning(u"something broke while creating new database tables:"
                        u"\n%s", e)

    if db_buildversion < 21000:
        yield parse_start()
        for store in Store.objects.iterator():
            try:
                yield parse_store(store)
                yield import_suggestions(store)
            except Exception, e:
                logging.warning(u"Something broke while parsing %s:\n%s",
                                store, e)

        yield parse_end()
        save_pootle_version(21000)

    if db_buildversion < 22000:
        flush_checks = not needs_toolkit_upgrade
        yield update_tables_22000(flush_checks)

    # Since :func:`update_stats_21060` works with the :cls:`TranslationProject`
    # model, this has to go after upgrading the DB tables, otherwise the model
    # and DB table definitions don't match.
    if db_buildversion < 21060:
        yield update_stats_21060()

    if tt_buildversion < 12008:
        yield update_ts_tt_12008()

    if needs_toolkit_upgrade:
        # Let's clear stale quality checks data. We can only do that safely if
        # the db schema is already up to date.
        yield update_toolkit_version()
    elif tt_buildversion != sys.maxint:
        # only need to update the toolkit version, not do the upgrade
        save_toolkit_version()

    # First time to visit the front page all stats for projects and
    # languages will be calculated which can take forever, since users
    # don't like webpages that take forever let's precalculate the
    # stats here (copied from dbinit)
    yield stats_start()

    for language in Language.objects.iterator():
        yield stats_language(language)

    for project in Project.objects.iterator():
        yield stats_project(project)

    yield stats_end()

    yield footer()

    # Bring back stdout
    sys.stdout = stdout

    return
