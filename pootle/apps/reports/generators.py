# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import codecs
import logging
import os

from subprocess import call

from django.conf import settings
from django.template.loader import render_to_string


logger = logging.getLogger(__name__)


class HTMLGenerator(object):
    extension = 'html'
    media_type = 'text/html'
    name = 'HTML'
    template_name = 'invoices/invoice.html'

    @staticmethod
    def is_configured():
        return True

    def generate(self, filepath, context, **kwargs):
        """Generates the HTML invoice and writes it to disk.

        :param filepath: absolute path where the invoice will be generated.
        :param context: dictionary with rendering context data.
        """
        html = render_to_string(self.template_name, context)
        codecs.open(filepath, 'w', 'utf-8').write(html)
        return True


class PDFGenerator(object):
    extension = 'pdf'
    media_type = 'application/pdf'
    name = 'PDF'

    @staticmethod
    def is_configured():
        phantomjs_bin = settings.POOTLE_INVOICES_PHANTOMJS_BIN
        if phantomjs_bin is None or not os.path.exists(phantomjs_bin):
            logger.warn(
                'NOTICE: settings.POOTLE_INVOICES_PHANTOMJS_BIN not defined or'
                'nothing found in the specified path. PDFs will not be generated.'
            )
            return False
        return True

    def generate(self, filepath, context, **kwargs):
        """Generates the PDF invoice and writes it to disk.

        :param filepath: absolute path where the invoice will be generated.
        :param context: dictionary with rendering context data.
        """
        html_filepath = filepath.replace('.pdf', '.html')
        if not os.path.exists(html_filepath):
            logger.info('HTML file does not exist: %s.\n'
                        'PDF will not be generated.' % html_filepath)
            return False

        html2pdf_js = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                   'html2pdf.js')
        exit_code = call([settings.POOTLE_INVOICES_PHANTOMJS_BIN, html2pdf_js,
                          html_filepath, filepath])
        if exit_code:
            logger.debug('Script exited with code: %s' % exit_code)
            return False

        return True
