#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
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

"""Extension action to generate Mozilla language packs (XPI)

This extension action uses the mozilla-l10n configuration files and repository
structure, but implements the necessary actions itself in Python, rather than
run the shell scripts that are provided in that Git repository.

"""

import fcntl
import os
import shutil
from subprocess import CalledProcessError

from django.conf import settings

from pootle.scripts.actions import DownloadAction
from pootle_store.util import absolute_real_path

from moztarball import (AURORA, MOZL10N, MozillaAction, getLogger, tempdir,
                        merge_po2moz)
from buildxpi import build_xpi


logger = getLogger(__name__)


class MozillaBuildLangpackAction(MozillaAction, DownloadAction):
    """Build Mozilla language pack for Firefox."""

    def __init__(self, **kwargs):
        super(MozillaBuildLangpackAction, self).__init__(**kwargs)
        self.icon = "icon-update-templates"
        self.permission = "administrate"

    def run(self, path, root, tpdir,  # pylint: disable=R0913,R0914
            language, project, vc_root, **kwargs):
        """Generate a Mozilla language pack XPI."""

        with tempdir() as l10ndir:
            try:
                merge_po2moz(vc_root, root, l10ndir, language, project)
            except EnvironmentError as e:
                logger.debug_exception(e)
                self.set_error(e)
                return

            aurora = os.path.join(vc_root, AURORA)
            mozl10n = os.path.join(vc_root, MOZL10N)

            def docopyfile(sourcefile, destfile):
                if os.path.exists(sourcefile):
                    destdir = os.path.join(l10ndir, language,
                                           os.path.dirname(destfile))
                    basename = os.path.basename(destfile)
                    if not os.path.isdir(destdir):
                        logger.debug("creating '%s' directory", destdir)
                        os.makedirs(destdir)
                    logger.debug("copying '%s' to '%s'", sourcefile,
                                 os.path.join(destdir, basename))
                    shutil.copy2(sourcefile, destdir)
                else:
                    logger.warning('unable to find %s', sourcefile)

            def copyaurorafile(filename):
                """Copy a file from VC source to L10n build directory"""
                split = filename.find(os.sep)
                sourcefile = os.path.join(aurora, filename[:split],
                                          'locales/en-US',
                                          filename[split + 1:])
                docopyfile(sourcefile, filename)

            def copyl10nfile(filename):
                """Copy a file from VC source to L10n build directory"""
                sourcefile = os.path.join(mozl10n, language, filename)
                if os.path.exists(sourcefile):
                    docopyfile(sourcefile, filename)
                else:
                    copyaurorafile(filename)


            def copyfileifmissing(filename):
                """Copy a file only if needed."""
                destfile = os.path.join(l10ndir, language, 'toolkit',
                                        filename)
                if not os.path.exists(destfile):
                    copyaurorafile(filename)

            try:
                # from mozilla-l10n/.ttk/default/build.sh
                copyfileifmissing('toolkit/chrome/mozapps/help/'
                                  'welcome.xhtml')
                copyfileifmissing('toolkit/chrome/mozapps/help/'
                                  'help-toc.rdf')
                copyaurorafile('browser/firefox-l10n.js')
                copyaurorafile('browser/profile/chrome/userChrome-example.css')
                copyaurorafile('browser/profile/chrome/userContent-example.css')
                copyl10nfile('browser/chrome/browser-region/region.properties')
                copyfileifmissing('toolkit/chrome/global/intl.css')
                # This one needs special approval but we need it
                # to pass and compile
                copyfileifmissing('browser/searchplugins/list.txt')

                with tempdir() as xpidir:

                    # Attempting to run build_xpi concurrently can fail,
                    # so lock it
                    lock_filename = os.path.join(aurora,
                                                 ".langpack_action_lock")
                    lock = open(lock_filename, "w")
                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX)

                    xpifile = build_xpi(l10nbase=l10ndir, srcdir=aurora,
                                        outputdir=xpidir, langs=[language],
                                        product='browser')[0]

                    if xpifile:
                        xpiname = '%s-%s.xpi' % (project, language)
                        newname = os.path.join(root, project, language,
                                               xpiname)
                        logger.debug("copying '%s' to '%s'",
                                     xpifile, newname)
                        shutil.move(xpifile, newname)
                        self.set_error(self.set_download_file(path,
                                                              newname))
                        os.remove(newname)


                    self.set_output(_("Finished building the language "
                                      "pack, click on the download "
                                      "link to download it."))

                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
                    lock.close()

            except (EnvironmentError, CalledProcessError) as e:
                logger.debug_exception(e)
                self.set_error(e)
                return


MozillaBuildLangpackAction.moztar = MozillaBuildLangpackAction(
                                            category="Mozilla",
                                            title="Build language pack")


class MozillaDownloadLangpackAction(DownloadAction, MozillaAction):
    """Download Mozilla language pack for Firefox."""

    def __init__(self, **kwargs):
        super(MozillaDownloadLangpackAction, self).__init__(**kwargs)
        self.permission = "archive"
        self.nosync = True

    def is_active(self, request):
        project = request.translation_project.project.code
        language = request.translation_project.language.code
        xpi_file = os.path.join('POOTLE_EXPORT',
                                project, language,
                                '%s-%s.xpi' % (project, language))
        abs_xpi_file = absolute_real_path(xpi_file)
        if not os.path.exists(abs_xpi_file):
            return False
        else:
            return super(MozillaDownloadLangpackAction, self).is_active(request)

    def run(self, path, root, tpdir,  # pylint: disable=R0913,R0914
            language, project, vc_root, **kwargs):
        """Download a Mozilla language pack XPI."""
        xpi_file = os.path.join('POOTLE_EXPORT',
                                project, language,
                                '%s-%s.xpi' % (project, language))
        self._dl_path[path.pootle_path] = xpi_file


MozillaDownloadLangpackAction.moztar = MozillaDownloadLangpackAction(
                                            category="Mozilla",
                                            title="Download language pack")
