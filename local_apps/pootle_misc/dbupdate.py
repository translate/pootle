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
from pootle_store.models import Store
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_misc.dbinit import stats_start, stats_language, stats_project, stats_end

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
    en, created = Language.objects.get_or_create(code='en', fullname='English', nplurals=2)
    field.default = en.id
    db.add_column(table_name, field.name, field)
    db.create_index(table_name, (field.name + '_id',))
    return text

def parse_start():
    text = u"""
    <p>%s</p>
    <ul>
    """ % _('Pootle will now import all the translations into the database. It could take a long time.')
    return text

def import_suggestions(store):
    try:
        logging.info("Importing suggestions for %s if any.", store.real_path)
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
        logging.info("Importing units from %s", store.real_path)
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
    """  % { 'endmsg': _('Pootle initialized the database. You will be redirected to the front page in 10 seconds.') }
    return text

def staggered_update(db_buildversion):
    """Update pootle database, while displaying progress report for each step"""

    # django's syncdb command prints progress reports to stdout, but
    # mod_wsgi doesn't like stdout, so we reroute to stderr
    stdout = sys.stdout
    sys.stdout = sys.stderr

    yield header(db_buildversion)

    ############## version specific updates ############

    if db_buildversion < 20030:
        yield update_permissions_20030()

    # build missing tables
    yield syncdb()

    if db_buildversion < 21000:
        yield update_tables_21000()
        Directory.objects.root.get_or_make_subdir('projects')
        for project in Project.objects.iterator():
            # saving should force project to update it's directory property
            try:
                project.save()
            except Exception, e:
                logging.warning("something broke while upgrading %s:\n%s", project.pootle_path, str(e))

        yield parse_start()
        for store in Store.objects.iterator():
            try:
                store.translation_project = store.parent.get_translationproject()
                store.save()
                yield parse_store(store)
                yield import_suggestions(store)
            except Exception, e:
                logging.warning("something broke while upgrading %s:\n%s", store.pootle_path, str(e))
        yield parse_end()

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
