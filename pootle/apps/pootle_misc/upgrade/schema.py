#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
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

"""Database schema upgrade code.

This is legacy code that only performs upgrades up to version 2.5. Any
future schema migrations are handled entirely by South.
"""

import logging

from django.core.management import call_command


def update_tables_22000():
    logging.info("Updating existing database tables")

    from django.db import models

    from south.db import db

    from pootle_language.models import Language
    from pootle_misc.siteconfig import load_site_config
    from pootle_project.models import Project
    from pootle_statistics.models import Submission
    from pootle_store.models import QualityCheck, Store, Suggestion, Unit
    from pootle_translationproject.models import TranslationProject

    # For the sake of South bug 313, we set the default for these fields here:
    # See http://south.aeracode.org/ticket/313
    table_name = Suggestion._meta.db_table
    field = Suggestion._meta.get_field('translator_comment_f')
    field.default = u''
    db.add_column(table_name, field.name, field)

    table_name = Language._meta.db_table
    field = Language._meta.get_field('description')
    field.default = u''
    db.add_column(table_name, field.name, field)

    field = models.TextField(default=u'', editable=False, blank=True)
    db.add_column(table_name, 'description_html', field)

    table_name = TranslationProject._meta.db_table
    field = TranslationProject._meta.get_field('description')
    field.default = u''
    db.add_column(table_name, field.name, field)

    field = models.TextField(default=u'', editable=False, blank=True)
    db.add_column(table_name, 'description_html', field)

    table_name = Project._meta.db_table
    field = Project._meta.get_field('report_target')
    field.default = u''
    db.add_column(table_name, field.name, field)

    field = models.TextField(default=u'', editable=False, blank=True)
    db.add_column(table_name, 'description_html', field)

    table_name = QualityCheck._meta.db_table
    field = QualityCheck._meta.get_field('category')
    db.add_column(table_name, field.name, field)
    # Delete all 'hassuggestion' failures, since we don't actually use them
    # See bug 2412.
    QualityCheck.objects.filter(name="hassuggestion").delete()

    table_name = Submission._meta.db_table
    for field_name in ('unit', 'field', 'type', 'old_value', 'new_value'):
        field = Submission._meta.get_field(field_name)
        db.add_column(table_name, field.name, field)

    table_name = Unit._meta.db_table
    for field_name in ('submitted_by', 'submitted_on', 'commented_by',
                       'commented_on'):
        field = Unit._meta.get_field(field_name)
        db.add_column(table_name, field.name, field)

    table_name = Store._meta.db_table
    field = Store._meta.get_field('sync_time')
    db.add_column(table_name, field.name, field)

    # Save the legacy buildversion using djblets.
    config = load_site_config()
    config.set('POOTLE_BUILDVERSION', 22000)
    config.save()
    logging.info("Database now at Pootle build 22000")


def staggered_update(db_buildversion):
    """Updates Pootle's database schema in steps."""

    # Build missing tables
    try:
        logging.info("Creating missing database tables")

        call_command('syncdb', interactive=False)
    except Exception as e:
        logging.warning(u"Something broke while creating new database tables:"
                        u"\n%s", e)

    if db_buildversion < 22000:
        update_tables_22000()
