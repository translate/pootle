#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
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

import sys
import logging

from django.core.management import call_command

from pootle.i18n.gettext import ugettext as _
from pootle.i18n.gettext import ungettext

from pootle_app.models import Directory
from pootle_store.models import Store, QualityCheck, CHECKED, PARSED
from pootle_store.util import OBSOLETE
from pootle_misc.util import deletefromcache
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject
from pootle_misc.dbinit import stats_start, stats_language, stats_project, stats_end

def flush_quality_checks():
    """reverts stores to unchecked state. if store has false positives
    marked updates quality checks keeping false postivies intact"""
    for store in Store.objects.filter(state=CHECKED).iterator():
        store_checks = QualityCheck.objects.filter(unit__store=store)
        false_positives = store_checks.filter(false_positive=True).count()
        if false_positives:
            logging.debug("%s has false positives, updating quality checks", store.pootle_path)
            for unit in store.units.iterator():
                unit.update_qualitychecks(keep_false_positives=True)
        else:
            logging.debug("%s has no false positives, deleting checks", store.pootle_path)
            store_checks.delete()
            store.state = PARSED
            store.save()

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
    """ % {'title': _('Pootle: Update'),
           'msg': _('Database tables are currently at build version %d. Pootle will now update the database.', db_buildversion)}
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
    contenttype, created = ContentType.objects.get_or_create(app_label="pootle_app", model="directory")
    for permission in Permission.objects.filter(content_type__name='pootle').iterator():
        permission.content_type = contenttype
        permission.save()
    contenttype.name = 'pootle'
    contenttype.save()
    return text

def update_tables_21000():
    text = u"""
    <p>%s</p>
    """ % _('Updating existing database tables...')
    logging.info("Updating existing database tables")
    from south.db import db
    #raise ImportError
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
        # we can't allow translation project detection to kick in yet so let's create en manually
        en = Language(code='en', fullname='English', nplurals=2, pluralequation="(n != 1)")
        en.directory = Directory.objects.root.get_or_make_subdir(en.code)
        en.save_base(raw=True)
    field.default = en.id
    db.add_column(table_name, field.name, field)
    db.create_index(table_name, (field.name + '_id',))
    return text

def update_qualitychecks_21040():
    text = """
    <p>%s</p>
    """ % _('Removing quality checks, will be recalculated on demand...')
    logging.info("Fixing quality checks")
    flush_quality_checks()
    return text

def update_stats_21060():
    text = """
    <p>%s</p>
    """ %_('Removing potentially incorrect cached stats, will be recalculated...')
    logging.info('flushing cached stats')
    for tp in TranslationProject.objects.filter(stores__unit__state=OBSOLETE).distinct().iterator():
        deletefromcache(tp, ["getquickstats", "getcompletestats", "get_mtime", "has_suggestions"])
    return text

def update_ts_tt_12008():
    text = """
    <p>%s</p>
    """ %_('Reparsing Qt ts files...')
    logging.info('reparsing qt ts')
    for store in Store.objects.filter(state__gt=PARSED,
                                      translation_project__project__localfiletype='ts',
                                      file__iendswith='.ts').iterator():
        store.sync(update_translation=True)
        store.update(update_structure=True, update_translation=True, conservative=False)
    return text

def parse_start():
    text = u"""
    <p>%s</p>
    <ul>
    """ % _('Pootle will now import all the translations into the database. It could take a long time.')
    return text

def import_suggestions(store):
    try:
        logging.info(u"Importing suggestions for %s if any.", store.real_path)
        store.import_pending()
        count = store.has_suggestions()
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
    """ % {'endmsg': _('Pootle initialized the database. You will be redirected to the front page in 10 seconds.')}
    return text

def staggered_update(db_buildversion, tt_buildversion):
    """Update pootle database, while displaying progress report for each step"""
    # django's syncdb command prints progress reports to stdout, but
    # mod_wsgi doesn't like stdout, so we reroute to stderr
    stdout = sys.stdout
    sys.stdout = sys.stderr

    yield header(db_buildversion)

    ############## version specific updates ############

    if db_buildversion < 20030:
        yield update_permissions_20030()

    if db_buildversion < 21000:
        try:
            yield update_tables_21000()
        except Exception, e:
            logging.warning(u"something broke while upgrading database tables:\n%s", e)

        logging.info("creating project directories")
        Directory.objects.root.get_or_make_subdir('projects')
        for project in Project.objects.iterator():
            # saving should force project to update it's directory property
            try:
                project.save()
            except Exception, e:
                logging.warning(u"something broke while upgrading %s:\n%s", project, e)

        logging.info("associating stores with translation projects")
        for store in Store.objects.iterator():
            try:
                store.translation_project = store.parent.get_translationproject()
                store.save()
            except Exception, e:
                logging.warning(u"something broke while upgrading %s:\n%s", store.pootle_path, e)

    # build missing tables
    try:
        yield syncdb()
    except Exception, e:
        logging.warning(u"something broke while creating new database tables:\n%s", e)

    if db_buildversion < 21000:
        yield parse_start()
        for store in Store.objects.iterator():
            try:
                yield parse_store(store)
                yield import_suggestions(store)
            except Exception, e:
                logging.warning(u"something broke while parsing %s:\n%s", store, e)

        yield parse_end()

    if db_buildversion < 21040:
        yield update_qualitychecks_21040()

    if db_buildversion < 21060:
        yield update_stats_21060()

    if tt_buildversion < 12008:
        yield update_ts_tt_12008()

    # first time to visit the front page all stats for projects and
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
    # bring back stdout
    sys.stdout = stdout
    return
