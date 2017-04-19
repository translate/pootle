# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import time

from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache

from pootle.core.utils.timezone import make_aware
from pootle_misc.checks import run_given_filters
from pootle_store.constants import OBSOLETE
from pootle_store.models import QualityCheck, Unit
from pootle_store.unit import UnitProxy
from pootle_translationproject.models import TranslationProject


logger = logging.getLogger(__name__)


class CheckableUnit(UnitProxy):
    """CheckableUnit wraps a `Unit` values dictionary to provide a `Unit` like
    instance that can be used by UnitQualityCheck

    At a minimum the dict should contain source_f, target_f, store__id, and
    store__translation_project__id
    """

    @property
    def store(self):
        return self.store_id

    @property
    def tp(self):
        return self.store__translation_project_id

    @property
    def language_code(self):
        return self.store__translation_project__language__code


class UnitQualityCheck(object):

    def __init__(self, unit, checker, original_checks,
                 check_names, keep_false_positives=True):
        """Refreshes QualityChecks for a Unit

        As this class can work with either `Unit` or `CheckableUnit` it only
        uses a minimum of `Unit` attributes from `self.unit`.

        :param unit: an instance of Unit or CheckableUnit
        :param checker: a Checker for this Unit.
        :param original_checks: current QualityChecks for this Unit
        :param check_names: limit checks to given list of quality check names.
        :param keep_false_positives: when set to `False`, it will unmute any
            existing false positive checks.
        """
        self.checker = checker
        self.unit = unit
        self.original_checks = original_checks
        self.check_names = check_names
        self.keep_false_positives = keep_false_positives
        self.unmute_list = []

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
        return self.checks_qs.filter(name__in=checks)

    def unmute_checks(self, checks):
        """Unmute checks that should no longer be muted
        """
        return self.checks_qs.filter(
            name__in=checks, false_positive=True).update(false_positive=False)

    def update(self):
        """Update QualityChecks for a Unit, deleting and unmuting as appropriate.
        """
        # update the checks for this unit
        updated = self.update_checks()

        # delete any remaining checks that were only in the original list
        deleted = (
            self.original_checks and self.delete_checks(self.original_checks))

        # unmute any checks that have been marked for unmuting
        unmuted = (
            self.unmute_list and self.unmute_checks(self.unmute_list))

        return updated, deleted, unmuted

    def update_checks(self):
        """Compare self.original_checks to the Units calculated QualityCheck failures.

        Removes members of self.original_checks as they have been compared.
        """
        updated = False
        new_checks = []
        for name in self.check_failures.iterkeys():
            if name in self.original_checks:
                # keep false-positive checks if check is active
                unmute = (
                    self.original_checks[name]['false_positive']
                    and not self.keep_false_positives)
                if unmute:
                    self.unmute_list.append(name)
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
        return new_checks


class QualityCheckUpdater(object):

    def __init__(self, check_names=None, translation_project=None,
                 keep_false_positives=True, units=None):
        """Refreshes QualityChecks for Units

        :param check_names: limit checks to given list of quality check names.
        :param translation_project: an instance of `TranslationProject` to
            restrict the update to.
        :param keep_false_positives: when set to `False`, it will unmute any
            existing false positive checks.
        """

        self.check_names = check_names
        self.translation_project = translation_project
        self.keep_false_positives = keep_false_positives
        self.stores = set()
        self._store_to_expire = None
        self._units = None

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

    @cached_property
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
        units = Unit.objects.all()
        if self.translation_project is not None:
            units = units.filter(
                store__translation_project=self.translation_project)
        return units

    def clear_checks(self):
        QualityCheck.delete_unknown_checks()

    @lru_cache(maxsize=None)
    def get_checker(self, tp_pk):
        """Return the site QualityChecker or the QualityCheck associated with
        the a Unit's TP otherwise.
        """
        if self.translation_project:
            return self.translation_project.checker
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

    def update(self, clear=False):
        """Update/purge all QualityChecks for Units, and expire Store caches.
        """
        if clear:
            start = time.time()
            logger.debug("Clearing unknown checks...")
            self.clear_checks()
            logger.debug(
                "Cleared unknown checks in %s seconds",
                (time.time() - start))
        if not self._units:
            start = time.time()
            logger.debug("Deleting checks for untranslated units...")
            untrans = self.update_untranslated()
            if untrans:
                logger.debug(
                    "Deleted %s checks for untranslated units in %s seconds",
                    untrans, (time.time() - start))

        start = time.time()
        # logger.debug("Updating checks - this may take some time...")
        trans = self.update_translated()
        if trans:
            logger.debug(
                "Updated checks for %s units in %s seconds",
                trans, (time.time() - start))

    def update_translated_unit(self, unit, checker=None):
        """Update checks for a translated Unit
        """
        unit = CheckableUnit(unit)
        checker = UnitQualityCheck(
            unit,
            checker,
            self.checks.get(unit.id, {}),
            self.check_names,
            self.keep_false_positives)
        updated, deleted, unmuted = checker.update()
        if (updated or deleted or unmuted):
            self.expire_store_cache(unit.store)
        return updated, deleted, unmuted

    def update_translated(self):
        """Update checks for translated Units
        """
        unit_fields = [
            "id", "source_f", "target_f", "locations", "store_id"]

        tp_key = "store__translation_project_id"
        lang_code_key = "store__translation_project__language__code"
        if self.translation_project is None:
            unit_fields.append(tp_key)
            unit_fields.append(lang_code_key)

        checker = None
        if self.translation_project is not None:
            # we only need to get the checker once if TP is set
            checker = self.get_checker(self.translation_project.id)

        translated = (
            self.units.filter(state__gte=OBSOLETE)
                      .order_by("store", "index"))
        updated_count = 0
        _updated = []
        for unit in translated.values(*unit_fields).iterator():
            if self.translation_project is not None:
                # if TP is set then manually add TP.id to the Unit value dict
                unit[tp_key] = self.translation_project.id
                unit[lang_code_key] = self.translation_project.language.code
            if checker is None:
                checker = self.get_checker(unit[tp_key])
            if checker:
                updated, deleted, unmuted = self.update_translated_unit(unit, checker=checker)
                if (updated or deleted or unmuted):
                    updated_count += 1
                if updated:
                    _updated += updated
        if _updated:
            self.checks_qs.bulk_create(_updated)
        # clear the cache of the remaining Store
        self.expire_store_cache()
        return updated_count

    def update_untranslated(self):
        """Delete QualityChecks for untranslated Units
        """
        return self.checks_qs.exclude(unit__state__gte=OBSOLETE).delete()
