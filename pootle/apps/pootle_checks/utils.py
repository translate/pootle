# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging

from translate.filters import checks
from translate.filters.decorators import Category
from translate.lang import data

from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache

from pootle.core.signals import update_data
from pootle_store.constants import UNTRANSLATED
from pootle_store.models import QualityCheck, Unit
from pootle_store.unit import UnitProxy
from pootle_translationproject.models import TranslationProject

from .constants import (
    CATEGORY_CODES, CATEGORY_IDS, CATEGORY_NAMES,
    CHECK_NAMES, EXCLUDED_FILTERS)


logger = logging.getLogger(__name__)


class CheckableUnit(UnitProxy):
    """CheckableUnit wraps a `Unit` values dictionary to provide a `Unit` like
    instance that can be used by UnitQualityCheck

    At a minimum the dict should contain source_f, target_f, store__id, and
    store__translation_project__id
    """

    @property
    def store(self):
        return self.store__id

    @property
    def tp(self):
        return self.store__translation_project__id

    @property
    def language_code(self):
        return self.store__translation_project__language__code


class UnitQualityCheck(object):

    def __init__(self, unit, checker, original_checks, check_names):
        """Refreshes QualityChecks for a Unit

        As this class can work with either `Unit` or `CheckableUnit` it only
        uses a minimum of `Unit` attributes from `self.unit`.

        :param unit: an instance of Unit or CheckableUnit
        :param checker: a Checker for this Unit.
        :param original_checks: current QualityChecks for this Unit
        :param check_names: limit checks to given list of quality check names.
        """
        self.checker = checker
        self.unit = unit
        self.original_checks = original_checks
        self.check_names = check_names

    @cached_property
    def check_failures(self):
        """Current QualityCheck failure for the Unit
        """
        if self.check_names is None:
            return self.checker.run_filters(
                self.unit, categorised=True)
        return run_given_filters(
            self.checker, self.unit, self.check_names)

    @cached_property
    def checks_qs(self):
        """QualityCheck queryset for the Unit
        """
        return QualityCheck.objects.filter(unit=self.unit.id)

    def delete_checks(self, checks):
        """Delete checks that are no longer used.
        """
        return self.checks_qs.filter(name__in=checks).delete()

    def update(self):
        """Update QualityChecks for a Unit, deleting and unmuting as appropriate.
        """
        # update the checks for this unit
        updated = self.update_checks()

        # delete any remaining checks that were only in the original list
        deleted = (
            self.original_checks and self.delete_checks(self.original_checks))

        return (updated or deleted)

    def update_checks(self):
        """Compare self.original_checks to the Units calculated QualityCheck failures.

        Removes members of self.original_checks as they have been compared.
        """
        updated = False
        new_checks = []
        for name in self.check_failures.iterkeys():
            if name in self.original_checks:
                # if the check is valid remove from the list and continue
                del self.original_checks[name]
                continue
            # the check didnt exist previously - so create it
            new_checks.append(
                self.checks_qs.model(
                    unit_id=self.unit.id,
                    name=name,
                    message=self.check_failures[name]['message'],
                    category=self.check_failures[name]['category']))
            updated = True
        if new_checks:
            self.checks_qs.bulk_create(new_checks)
        return updated


class QualityCheckUpdater(object):

    def __init__(self, check_names=None, translation_project=None, units=None):
        """Refreshes QualityChecks for Units

        :param check_names: limit checks to given list of quality check names.
        :param translation_project: an instance of `TranslationProject` to
            restrict the update to.
        """

        self.check_names = check_names
        self.translation_project = translation_project
        self.stores = set()
        self._units = units
        self._store_to_expire = None
        self._updated_stores = {}

    @cached_property
    def checks(self):
        """Existing checks in the database for all units
        """
        checks = self.checks_qs
        check_keys = (
            'id', 'name', 'unit_id',
            'category', 'false_positive')

        if self.check_names is not None:
            checks = checks.filter(name__in=self.check_names)

        all_units_checks = {}
        for check in checks.values(*check_keys):
            all_units_checks.setdefault(
                check['unit_id'], {})[check['name']] = check
        return all_units_checks

    @property
    def checks_qs(self):
        """QualityCheck queryset for all units, restricted to TP if set
        """
        checks_qs = QualityCheck.objects.all()

        if self.translation_project is not None:
            tp_pk = self.translation_project.pk
            checks_qs = checks_qs.filter(
                unit__store__translation_project__pk=tp_pk)
        if self._units is not None:
            checks_qs = checks_qs.filter(
                unit_id__in=self._units.values_list("id", flat=True))
        return checks_qs

    @cached_property
    def units(self):
        """Result set of Units, restricted to TP if set
        """
        if self._units:
            return self._units
        units = Unit.objects.all()
        if self.translation_project is not None:
            units = units.filter(
                store__translation_project=self.translation_project)
        return units

    def clear_unknown_checks(self):
        QualityCheck.delete_unknown_checks()

    @lru_cache(maxsize=None)
    def get_checker(self, tp_pk):
        """Return the site QualityChecker or the QualityCheck associated with
        the a Unit's TP otherwise.
        """
        try:
            return TranslationProject.objects.get(id=tp_pk).checker
        except TranslationProject.DoesNotExist:
            # There seems to be a risk of dangling Stores with no TP
            logger.error("Missing TP (pk '%s'). No checker retrieved.", tp_pk)
            return None

    def expire_store_cache(self, store_pk=None):
        """Whenever a store_pk is found it is queued for cache expiry

        if a new store_pk is called the old one has its cache expired,
        and the new store_pk is saved

        call with None to expire the current Store's cache
        """
        if self._store_to_expire is None:
            # there is no Store set - queue it for expiry
            self._store_to_expire = store_pk
            return
        if store_pk == self._store_to_expire:
            # its the same Store that we saw last time
            return

        # remember the new store_pk
        self._store_to_expire = store_pk

    @property
    def tp_qs(self):
        return TranslationProject.objects.all()

    @property
    def updated_stores(self):
        return self._updated_stores

    def update(self):
        """Update/purge all QualityChecks for Units, and expire Store caches.
        """
        self.clear_unknown_checks()
        self.update_untranslated()
        self.update_translated()
        self.update_data()

    def update_data(self):
        if not self.updated_stores:
            return
        if self.translation_project:
            tps = {
                self.translation_project.id: self.translation_project}
        else:
            tps = self.tp_qs.filter(
                id__in=self.updated_stores.keys()).in_bulk()
        for tp, stores in self.updated_stores.items():
            tp = tps[tp]
            update_data.send(
                tp.__class__,
                instance=tp,
                object_list=tp.stores.filter(id__in=stores))
        del self.__dict__["checks"]
        self._updated_stores = {}

    def update_translated_unit(self, unit, checker=None):
        """Update checks for a translated Unit
        """
        unit = CheckableUnit(unit)
        checker = UnitQualityCheck(
            unit,
            checker,
            self.checks.get(unit.id, {}),
            self.check_names)
        if checker.update():
            self.update_store(unit.tp, unit.store)
            self.expire_store_cache(unit.store)
            return True
        return False

    def update_translated(self):
        """Update checks for translated Units
        """
        unit_fields = [
            "id", "source_f", "target_f", "locations", "store__id",
            "store__translation_project__language__code",
        ]

        tp_key = "store__translation_project__id"
        if self.translation_project is None:
            unit_fields.append(tp_key)

        checker = None
        if self.translation_project is not None:
            # we only need to get the checker once if TP is set
            checker = self.get_checker(self.translation_project.id)

        translated = (
            self.units.filter(state__gt=UNTRANSLATED)
                      .order_by("store", "index"))
        updated_count = 0
        for unit in translated.values(*unit_fields).iterator():
            if self.translation_project is not None:
                # if TP is set then manually add TP.id to the Unit value dict
                unit[tp_key] = self.translation_project.id
            if checker is None:
                checker = self.get_checker(unit[tp_key])
            if checker and self.update_translated_unit(unit, checker=checker):
                updated_count += 1
        # clear the cache of the remaining Store
        self.expire_store_cache()
        return updated_count

    def update_store(self, tp, store):
        self._updated_stores[tp] = (
            self._updated_stores.get(tp, set()))
        self._updated_stores[tp].add(store)

    def update_untranslated(self):
        """Delete QualityChecks for untranslated Units
        """
        untranslated = self.checks_qs.exclude(unit__state__gt=UNTRANSLATED)
        untranslated_stores = untranslated.values_list(
            "unit__store__translation_project", "unit__store").distinct()
        for tp, store in untranslated_stores.iterator():
            self.update_store(tp, store)
        return untranslated.delete()


def get_category_id(code):
    return CATEGORY_IDS.get(code)


def get_category_code(cid):
    return CATEGORY_CODES.get(cid)


def get_category_name(code):
    return unicode(CATEGORY_NAMES.get(code))


def run_given_filters(checker, unit, check_names=None):
    """Run all the tests in this suite.

    :rtype: Dictionary
    :return: Content of the dictionary is as follows::

       {'testname': {
           'message': message_or_exception,
           'category': failure_category
        }}

    Do some optimisation by caching some data of the unit for the
    benefit of :meth:`~TranslationChecker.run_test`.
    """
    if check_names is None:
        check_names = []

    checker.str1 = data.normalized_unicode(unit.source) or u""
    checker.str2 = data.normalized_unicode(unit.target) or u""
    checker.language_code = unit.language_code  # XXX: comes from `CheckableUnit`
    checker.hasplural = unit.hasplural()
    checker.locations = unit.getlocations()

    checker.results_cache = {}
    failures = {}

    for functionname in check_names:
        if isinstance(checker, checks.TeeChecker):
            for _checker in checker.checkers:
                filterfunction = getattr(_checker, functionname, None)
                if filterfunction:
                    checker = _checker
                    checker.str1 = data.normalized_unicode(unit.source) or u""
                    checker.str2 = data.normalized_unicode(unit.target) or u""
                    checker.language_code = unit.language_code
                    checker.hasplural = unit.hasplural()
                    checker.locations = unit.getlocations()
                    break
        else:
            filterfunction = getattr(checker, functionname, None)

        # This filterfunction may only be defined on another checker if
        # using TeeChecker
        if filterfunction is None:
            continue

        filtermessage = filterfunction.__doc__

        try:
            filterresult = checker.run_test(filterfunction, unit)
        except checks.FilterFailure as e:
            filterresult = False
            filtermessage = unicode(e)
        except Exception as e:
            if checker.errorhandler is None:
                raise ValueError("error in filter %s: %r, %r, %s" %
                                 (functionname, unit.source, unit.target, e))
            else:
                filterresult = checker.errorhandler(functionname, unit.source,
                                                    unit.target, e)

        if not filterresult:
            # We test some preconditions that aren't actually a cause for
            # failure
            if functionname in checker.defaultfilters:
                failures[functionname] = {
                    'message': filtermessage,
                    'category': checker.categories[functionname],
                }

    checker.results_cache = {}

    return failures


def get_qualitychecks():
    available_checks = {}

    checkers = [checker() for checker in checks.projectcheckers.values()]

    for checker in checkers:
        for filt in checker.defaultfilters:
            if filt not in EXCLUDED_FILTERS:
                # don't use an empty string because of
                # http://bugs.python.org/issue18190
                try:
                    getattr(checker, filt)(u'_', u'_')
                except Exception as e:
                    # FIXME there must be a better way to get a list of
                    # available checks.  Some error because we're not actually
                    # using them on real units.
                    logging.error("Problem with check filter '%s': %s",
                                  filt, e)
                    continue

        available_checks.update(checker.categories)

    return available_checks


def get_qualitycheck_schema(path_obj=None):
    d = {}
    checks = get_qualitychecks()

    for check, cat in checks.items():
        if cat not in d:
            d[cat] = {
                'code': cat,
                'name': get_category_code(cat),
                'title': get_category_name(cat),
                'checks': []
            }
        d[cat]['checks'].append({
            'code': check,
            'title': u"%s" % CHECK_NAMES.get(check, check),
            'url': path_obj.get_translate_url(check=check) if path_obj else ''
        })

    result = sorted([item for item in d.values()],
                    key=lambda x: x['code'],
                    reverse=True)

    return result


def get_qualitycheck_list(path_obj):
    """
    Returns list of checks sorted in alphabetical order
    but having critical checks first.
    """
    result = []
    checks = get_qualitychecks()

    for check, cat in checks.items():
        result.append({
            'code': check,
            'is_critical': cat == Category.CRITICAL,
            'title': u"%s" % CHECK_NAMES.get(check, check),
            'url': path_obj.get_translate_url(check=check)
        })

    def alphabetical_critical_first(item):
        critical_first = 0 if item['is_critical'] else 1
        return critical_first, item['title'].lower()

    result = sorted(result, key=alphabetical_critical_first)

    return result
