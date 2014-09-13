#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2014 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
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

import os
from optparse import make_option

from translate.filters.decorators import Category

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle_app.management.commands import PootleCommand
from pootle_statistics.models import Submission
from pootle_store.caching import count_words
from pootle_store.models import (QualityCheck, Suggestion, SuggestionStates,
                                 Unit)
from pootle_store.util import OBSOLETE, UNTRANSLATED, FUZZY, TRANSLATED


class Command(PootleCommand):
    help = "Allow stats to be refreshed manually."

    shared_option_list = (
        make_option("--calculate-checks", dest="calculate_checks",
                    action="store_true", help="Recalculate all quality checks"),
    )
    option_list = PootleCommand.option_list + shared_option_list

    def handle_noargs(self, *args, **kwargs):
        self._updated_tps = set()
        super(Command, self).handle_noargs(*args, **kwargs)
        self.update_translation_projects(self._updated_tps)

    def handle_store(self, store, **options):
        self.stdout.write("Processing %r" % (store))
        store.total_wordcount = 0
        store.translated_wordcount = 0
        store.fuzzy_wordcount = 0
        store.suggestion_count = Suggestion.objects.filter(
            unit__store=store,
            unit__state__gt=OBSOLETE,
            state=SuggestionStates.PENDING,
        ).count()

        for unit in store.units.all():
            wordcount = count_words(unit.source_f.strings)
            store.total_wordcount += wordcount
            if unit.state == TRANSLATED:
                store.translated_wordcount += wordcount
            elif unit.state == FUZZY:
                store.fuzzy_wordcount += wordcount

        try:
            last_unit = store.unit_set.latest('creation_time')
            # creation_time field has been added recently, so it can have NULL
            # value.
            if last_unit.creation_time is not None:
                store.last_unit = last_unit
        except Unit.DoesNotExist:
            pass

        units = store.unit_set.all().order_by('-submitted_on')[:1]
        try:
            store.last_submission = Submission.simple_objects.filter(
                unit=units[0]
            ).order_by('-creation_time')[0]
        except IndexError:
            pass

        if options["calculate_checks"]:
            self.stdout.write("Calculating checks for %r" % (store))
            store.update_qualitychecks(keep_false_positives=True)

            store.failing_critical_count = QualityCheck.objects.filter(
                unit__store=store,
                unit__state__gt=UNTRANSLATED,
                category=Category.CRITICAL,
                false_positive=False,
            ).values('unit').distinct().count()

        store.save()
        self._updated_tps.add(store.translation_project)

    def update_translation_projects(self, tps):
        def update(tp, col):
            setattr(tp, col, sum(getattr(store, col) for store in tp.stores.iterator()))

        self.stdout.write("\nProcessing translation projects...")

        for tp in tps:
            self.stdout.write("Processing %r" % (tp))
            update(tp, "total_wordcount")
            update(tp, "translated_wordcount")
            update(tp, "fuzzy_wordcount")
            update(tp, "suggestion_count")
            update(tp, "failing_critical_count")

            last_unit_store = tp.stores.latest('last_unit__creation_time')
            tp.last_unit = last_unit_store.last_unit

            try:
                last_sub_store = tp.stores.latest('last_submission__creation_time')
                tp.last_submission = last_sub_store.last_submission
            except Submission.DoesNotExist:
                pass

            tp.save()

        self.stdout.write("\nSuccessfully updated translation counts.")
