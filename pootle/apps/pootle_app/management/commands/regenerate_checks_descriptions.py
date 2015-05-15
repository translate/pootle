#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import codecs
import os

from translate.filters.checks import TeeChecker

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.conf import settings
from django.core.management.base import CommandError, NoArgsCommand

from pootle_misc.checks import check_names, excluded_filters


class Command(NoArgsCommand):
    help = 'Regenerate the Translate Toolkit quality checks descriptions.'

    def handle_noargs(self, **options):
        """Regenerate all the Translate Toolkit quality checks descriptions.

        The resulting HTML is save on the 'checks/_ttk_descriptions.html'
        template so it can be rendered when Pootle displays the quality checks
        descriptions page.
        """
        try:
            from docutils.core import publish_parts
        except ImportError:
            raise CommandError("Please install missing 'docutils' dependency.")

        def get_check_description(name, filterfunc):
            """Get a HTML snippet for a specific quality check description.

            The quality check description is extracted from the check function
            docstring (which uses reStructuredText) and rendered using docutils
            to get the HTML snippet.
            """
            # Provide a header with an anchor to refer to.
            description = ('\n<h3 id="%s">%s</h3>\n\n' %
                           (name, unicode(check_names[name])))

            # Clean the leading whitespace on each docstring line so it gets
            # properly rendered.
            docstring = '\n'.join([line.strip()
                                   for line in filterfunc.__doc__.split('\n')])

            # Render the reStructuredText in the docstring into HTML.
            description += publish_parts(docstring, writer_name='html')['body']
            return description

        self.stdout.write('Regenerating Translate Toolkit quality checks '
                          'descriptions.')

        # Get a checker with the Translate Toolkit checks. Note that filters
        # that are not used in Pootle are excluded.
        filterdict = TeeChecker().getfilters(excludefilters=excluded_filters)

        filterdocs = [get_check_description(name, filterfunc)
                      for (name, filterfunc) in filterdict.iteritems()]

        filterdocs.sort()

        body = u'\n'.join(filterdocs)

        # Output the quality checks descriptions to the HTML file.
        filename = os.path.join(settings.WORKING_DIR,
                                'templates/help/_ttk_quality_checks.html')

        with codecs.open(filename, 'w', 'utf-8') as f:
            f.write(body)

        self.stdout.write('Done.')
