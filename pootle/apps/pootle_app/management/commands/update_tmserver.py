# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
from hashlib import md5

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from elasticsearch import Elasticsearch, helpers
from translate.storage import factory

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import dateparse
from django.utils.encoding import force_bytes

from pootle.core.utils import dateformat
from pootle_store.models import Unit
from pootle_translationproject.models import TranslationProject


BULK_CHUNK_SIZE = 5000


class BaseParser(object):

    def __init__(self, *args, **kwargs):
        """Initialize the parser."""
        self.stdout = kwargs.pop('stdout')
        self.INDEX_NAME = kwargs.pop('index', None)

    def get_units(self):
        """Gets the units to import and its total count."""
        raise NotImplementedError

    def get_unit_data(self, unit):
        """Return dict with data to import for a single unit."""
        raise NotImplementedError


class DBParser(BaseParser):

    def __init__(self, *args, **kwargs):
        super(DBParser, self).__init__(*args, **kwargs)

        self.exclude_disabled_projects = not kwargs.pop('disabled_projects')
        self.tp_pk = None

    def get_units(self):
        """Gets the units to import and its total count."""
        units_qs = (
            Unit.objects.exclude(target_f__isnull=True)
                        .exclude(target_f__exact='')
                        .filter(store__translation_project__pk=self.tp_pk)
                        .filter(revision__gt=self.last_indexed_revision))
        units_qs = units_qs.select_related(
            'change__submitted_by',
            'store',
            'store__translation_project__project',
            'store__translation_project__language')

        if self.exclude_disabled_projects:
            units_qs = units_qs.exclude(
                store__translation_project__project__disabled=True
            ).exclude(store__obsolete=True)

        units_qs = units_qs.values(
            'id',
            'revision',
            'source_f',
            'target_f',
            'change__submitted_on',
            'change__submitted_by__username',
            'change__submitted_by__full_name',
            'change__submitted_by__email',
            'store__translation_project__project__fullname',
            'store__pootle_path',
            'store__translation_project__language__code'
        ).order_by()

        return units_qs.iterator(), units_qs.count()

    def get_unit_data(self, unit):
        """Return dict with data to import for a single unit."""
        fullname = (unit['change__submitted_by__full_name'] or
                    unit['change__submitted_by__username'])

        email_md5 = None
        if unit['change__submitted_by__email']:
            email_md5 = md5(
                force_bytes(unit['change__submitted_by__email'])).hexdigest()

        iso_submitted_on = unit.get('change__submitted_on', None)

        display_submitted_on = None
        if iso_submitted_on:
            display_submitted_on = dateformat.format(
                dateparse.parse_datetime(str(iso_submitted_on))
            )

        return {
            '_index': self.INDEX_NAME,
            '_type': unit['store__translation_project__language__code'],
            '_id': unit['id'],
            'revision': int(unit['revision']),
            'project': unit['store__translation_project__project__fullname'],
            'path': unit['store__pootle_path'],
            'username': unit['change__submitted_by__username'],
            'fullname': fullname,
            'email_md5': email_md5,
            'source': unit['source_f'],
            'target': unit['target_f'],
            'iso_submitted_on': iso_submitted_on,
            'display_submitted_on': display_submitted_on,
        }


class FileParser(BaseParser):

    def __init__(self, *args, **kwargs):
        super(FileParser, self).__init__(*args, **kwargs)

        self.target_language = kwargs.pop('language', None)
        self.project = kwargs.pop('project', None)
        self.filenames = kwargs.pop('filenames')

    def get_units(self):
        """Gets the units to import and its total count."""
        units = []
        all_filenames = set()

        for filename in self.filenames:
            if not os.path.exists(filename):
                self.stdout.write("File %s doesn't exist. Skipping it." %
                                  filename)
                continue

            if os.path.isdir(filename):
                for dirpath, dirs_, fnames in os.walk(filename):
                    if (os.path.basename(dirpath) in
                        ["CVS", ".svn", "_darcs", ".git", ".hg", ".bzr"]):

                        continue

                    for f in fnames:
                        all_filenames.add(os.path.join(dirpath, f))
            else:
                all_filenames.add(filename)

        for filename in all_filenames:
            store = factory.getobject(filename)
            if not store.gettargetlanguage() and not self.target_language:
                raise CommandError("Unable to determine target language for "
                                   "'%s'. Try again specifying a fallback "
                                   "target language with --target-language" %
                                   filename)

            self.filename = filename
            units.extend([unit for unit in store.units if unit.istranslated()])

        return units, len(units)

    def get_unit_data(self, unit):
        """Return dict with data to import for a single unit."""
        target_language = unit.gettargetlanguage()
        if target_language is None:
            target_language = self.target_language

        return {
            '_index': self.INDEX_NAME,
            '_type': target_language,
            '_id': unit.getid(),
            'revision': 0,
            'project': self.project,
            'path': self.filename,
            'username': None,
            'fullname': None,
            'email_md5': None,
            'source': unit.source,
            'target': unit.target,
            'iso_submitted_on': None,
            'display_submitted_on': None,
        }


class Command(BaseCommand):
    help = "Load Translation Memory with translations"

    def add_arguments(self, parser):
        parser.add_argument(
            '--refresh',
            action='store_true',
            dest='refresh',
            default=False,
            help='Process all items, not just the new ones, so '
                 'existing translations are refreshed'
        )
        parser.add_argument(
            '--rebuild',
            action='store_true',
            dest='rebuild',
            default=False,
            help='Drop the entire TM on start and update everything '
                 'from scratch'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Report the number of translations to index and quit'
        )

        # Local TM specific options.
        local = parser.add_argument_group('Local TM', 'Pootle Local '
                                          'Translation Memory')
        local.add_argument(
            '--include-disabled-projects',
            action='store_true',
            dest='disabled_projects',
            default=False,
            help='Add translations from disabled projects'
        )

        # External TM specific options.
        external = parser.add_argument_group('External TM', 'Pootle External '
                                             'Translation Memory')
        external.add_argument(
            nargs='*',
            dest='files',
            help='Translation memory files',
        )
        external.add_argument(
            '--tm',
            action='store',
            dest='tm',
            default='local',
            help="TM to use. TM must exist on settings. TM will be "
                 "created on the server if it doesn't exist"
        )
        external.add_argument(
            '--target-language',
            action='store',
            dest='target_language',
            default='',
            help="Target language to fallback to use in case it can't "
                 "be guessed for any of the input files."
        )
        external.add_argument(
            '--display-name',
            action='store',
            dest='project',
            default='',
            help='Name used when displaying TM matches for these '
                 'translations.'
        )

    def _parse_translations(self, **options):
        units, total = self.parser.get_units()

        if total == 0:
            self.stdout.write("No translations to index")
            return

        self.stdout.write("%s translations to index" % total)

        if options['dry_run']:
            return

        self.stdout.write("")

        i = 0
        for i, unit in enumerate(units, start=1):
            if (i % 1000 == 0) or (i == total):
                percent = "%.1f" % (i * 100.0 / total)
                self.stdout.write("%s (%s%%)" % (i, percent), ending='\r')
                self.stdout.flush()

            yield self.parser.get_unit_data(unit)

        if i != total:
            self.stdout.write("Expected %d, loaded %d." % (total, i))

    def _initialize(self, **options):
        if not settings.POOTLE_TM_SERVER:
            raise CommandError('POOTLE_TM_SERVER setting is missing.')

        try:
            self.tm_settings = settings.POOTLE_TM_SERVER[options['tm']]
        except KeyError:
            raise CommandError("Translation Memory '%s' is not defined in the "
                               "POOTLE_TM_SERVER setting. Please ensure it "
                               "exists and double-check you typed it "
                               "correctly." % options['tm'])

        self.INDEX_NAME = self.tm_settings['INDEX_NAME']
        self.is_local_tm = options['tm'] == 'local'

        self.es = Elasticsearch([
            {
                'host': self.tm_settings['HOST'],
                'port': self.tm_settings['PORT'],
            }], retry_on_timeout=True
        )

        # If files to import have been provided.
        if options['files']:
            if self.is_local_tm:
                raise CommandError('You cannot add translations from files to '
                                   'a local TM.')

            if not options['project']:
                raise CommandError('You must specify a project name with '
                                   '--display-name.')
            self.parser = FileParser(stdout=self.stdout, index=self.INDEX_NAME,
                                     filenames=options['files'],
                                     language=options['target_language'],
                                     project=options['project'])
        elif not self.is_local_tm:
            raise CommandError('You cannot add translations from database to '
                               'an external TM.')
        else:
            self.parser = DBParser(
                stdout=self.stdout, index=self.INDEX_NAME,
                disabled_projects=options['disabled_projects'])

    def _set_latest_indexed_revision(self, **options):
        self.last_indexed_revision = -1

        if (not options['rebuild'] and
            not options['refresh'] and
            self.es.indices.exists(self.INDEX_NAME)):

            result = self.es.search(
                index=self.INDEX_NAME,
                body={
                    'aggs': {
                        'max_revision': {
                            'max': {
                                'field': 'revision'
                            }
                        }
                    }
                }
            )
            self.last_indexed_revision = \
                result['aggregations']['max_revision']['value'] or -1

        self.parser.last_indexed_revision = self.last_indexed_revision

        self.stdout.write("Last indexed revision = %s" %
                          self.last_indexed_revision)

    def handle(self, **options):
        self._initialize(**options)

        if (options['rebuild'] and
            not options['dry_run'] and
            self.es.indices.exists(self.INDEX_NAME)):

            self.es.indices.delete(index=self.INDEX_NAME)

        if (not options['dry_run'] and
            not self.es.indices.exists(self.INDEX_NAME)):

            self.es.indices.create(index=self.INDEX_NAME)

        if self.is_local_tm:
            self._set_latest_indexed_revision(**options)

        if isinstance(self.parser, FileParser):
            helpers.bulk(self.es, self._parse_translations(**options))
            return

        # If we are parsing from DB.
        tp_qs = TranslationProject.objects.all()

        if options['disabled_projects']:
            tp_qs = tp_qs.exclude(project__disabled=True)

        for tp in tp_qs:
            self.parser.tp_pk = tp.pk
            helpers.bulk(self.es, self._parse_translations(**options))
