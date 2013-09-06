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

from __future__ import absolute_import

import logging

from django.core.management import call_command

from pootle_language.models import Language
from pootle_project.models import Project
from pootle_store.models import Store

from . import save_legacy_pootle_version


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
        from pootle_app.models import Directory

        # We can't allow translation project detection to kick in yet so let's
        # create en manually
        en = Language(code='en', fullname='English', nplurals=2,
                      pluralequation="(n != 1)")
        en.directory = Directory.objects.root.get_or_make_subdir(en.code)
        en.save_base(raw=True)
    field.default = en.id
    db.add_column(table_name, field.name, field)
    db.create_index(table_name, (field.name + '_id',))

    save_legacy_pootle_version(21000)


def update_tables_22000():
    logging.info("Updating existing database tables")

    from south.db import db

    from pootle_store.models import Suggestion
    from pootle_translationproject.models import TranslationProject
    from pootle_statistics.models import Submission
    from pootle_store.models import QualityCheck, Unit

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

    save_legacy_pootle_version(22000)


def staggered_update(db_buildversion):
    """Updates Pootle's database schema in steps."""

    if db_buildversion < 21000:
        try:
            update_tables_21000()
        except Exception as e:
            logging.warning(u"Something broke while upgrading database "
                            u"tables:\n%s", e)
            #TODO: should we continue?

    # Build missing tables
    try:
        logging.info("Creating missing database tables")

        call_command('syncdb', interactive=False)
    except Exception as e:
        logging.warning(u"Something broke while creating new database tables:"
                        u"\n%s", e)

    if db_buildversion < 22000:
        update_tables_22000()
