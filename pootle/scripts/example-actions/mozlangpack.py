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

from __future__ import with_statement

import errno
import logging
import os
import shutil
import subprocess

from contextlib import contextmanager
from datetime import datetime
from tempfile import mkdtemp

from translate.convert import po2moz

from pootle.scripts.actions import DownloadAction, TranslationProjectAction

from buildxpi import build_xpi

MOZL10N = "mozilla-l10n"
AURORA = "mozilla-aurora"


@contextmanager
def tempdir():
    """Context manager for creating and deleting a temporary directory."""
    tmpdir = mkdtemp()
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir)


def get_version(vc_root):
    """Get Mozilla version from browser (since mobile has no version.txt)"""
    vfile = os.path.join(vc_root, AURORA, 'browser', 'config', 'version.txt')
    try:
        with open(vfile) as vfh:
            version = vfh.readline()
    except IOError:
        logging.exception("Unable to get version from %s", vfile)
        return "aurora"

    return version.strip()


def get_phases(root, vc_root, workdir, language, project):
    """
    Create repository-layout tree of PO files from translations;
    (re)raises IOError, OSError, and/or shutil.Error from open, os.mkdirs,
    and/or shutil.copyfile
    """

    phasefile = os.path.join(vc_root, MOZL10N, ".ttk", project,
                             project + ".phaselist")
    tdirs = {}
    try:
        with open(phasefile) as pfile:
            for phase in [line.strip().split() for line in pfile]:
                path = phase[1]
                if path.startswith('./'):
                    path = path[2:]
                source = os.path.join(root, project, language, phase[0], path)
                target = os.path.join(workdir, language, path)
                tdir = target[:target.rfind(os.sep)]
                if not tdir in tdirs:
                    logging.debug("creating '%s' directory", tdir)
                    try:
                        os.makedirs(tdir)
                    except OSError, e:
                        if e.errno == errno.EEXIST and os.path.isdir(tdir):
                            pass
                        else:
                            raise
                    while tdir:
                        tdirs[tdir] = True
                        tdir = tdir[:tdir.rfind(os.sep)]
                logging.debug("copying '%s' to '%s'", source, target)
                try:
                    shutil.copyfile(source, target)
                except (shutil.Error, IOError):
                    logging.exception("Cannot update %s", target)
                    raise
    except IOError:
        logging.exception("Cannot get phases from %s", phasefile)
        raise


class MozillaLangpackAction(DownloadAction, TranslationProjectAction):
    """Download Mozilla language pack for Firefox"""

    def run(self, path, root, tpdir,  # pylint: disable=R0913
            language, project, vc_root, **kwargs):
        """Generate a Mozilla language pack XPI"""

        with tempdir() as podir:
            try:
                get_phases(root, vc_root, podir, language, project)
            except (IOError, OSError, shutil.Error), e:
                self.set_error(e)
                return

            with tempdir() as l10ndir:
                po2moz.main(['--progress=none', '-l', language,
                            '-t', os.path.join(vc_root, MOZL10N,
                                               'templates-en-US'),
                            '-i', os.path.join(podir, language),
                            '-o', os.path.join(l10ndir, language)])

                with tempdir() as xpidir:
                    try:
                        xpifile = build_xpi(l10nbase=l10ndir,
                                            srcdir=os.path.join(vc_root,
                                                                AURORA),
                                            outputdir=xpidir, lang=language,
                                            product='browser')
                    except Exception, e:
                        self.set_error(e)
                        return

                if xpifile:
                    error += self.set_download_file(path, xpifile)

        self.set_output(output)
        self.set_error(error)


MozillaLangpackAction.moztar = MozillaLangpackAction(category="Other actions",
                                                     title="Download langpack")
