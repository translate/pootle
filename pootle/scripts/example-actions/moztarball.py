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

"""Extension action to generate Mozilla language tar archives

This extension action uses the mozilla-l10n configuration files and repository
structure, but implements the necessary actions itself in Python, rather than
run the shell scripts that are provided in that Git repository.

"""

from __future__ import with_statement

import contextlib
import errno
import logging
import os
import shutil
import subprocess
from tempfile import mkdtemp

from translate.convert import po2moz
from pootle.scripts.actions import DownloadAction, TranslationProjectAction

MOZ = "mozilla-l10n"


@contextlib.contextmanager
def tempdir():
    """Context manager for creating and deleting a temporary directory."""
    tmpdir = mkdtemp()
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir)


def get_phases(root, vc_root, workdir, language, project):
    """
    Create repository-layout tree of PO files from translations;
    (re)raises IOError, OSError, and/or shutil.Error from open, os.mkdirs,
    and/or shutil.copyfile
    """

    phasefile = os.path.join(vc_root, MOZ, ".ttk", project,
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


class MozillaTarballAction(DownloadAction, TranslationProjectAction):
    """Download Mozilla language properties tarball"""

    def run(self, path, root, tpdir,  # pylint: disable=R0913
            language, project, vc_root, **kwargs):
        """Generate a Mozilla language properties tarball"""

        with tempdir() as podir:
            try:
                get_phases(root, vc_root, podir, language, project)
            except (IOError, OSError, shutil.Error), e:
                self.set_error(e)
                return

            templates = os.path.join(vc_root, MOZ, 'templates-en-US')

            with tempdir() as tardir:
                po2moz.main(['--progress=none', '-l', language,
                            '-t', templates,
                            '-i', os.path.join(podir, language),
                            '-o', os.path.join(tardir, language)])

                tarfile = os.path.join(root, tpdir, language + ".tar")

                process = subprocess.Popen(['tar', '-c', '-C', tardir,
                                            '-f', tarfile, language],
                                           universal_newlines=True,
                                           close_fds=(os.name != 'nt'),
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
                (output, error) = process.communicate()
                if process.returncode > 0:
                    error += ("\n [tar exited with status %d]\n" %
                              process.returncode)
                elif process.returncode < 0:
                    error += ("\n [tar killed by signal %d]\n" %
                              -process.returncode)
                else:
                    self.set_download_file(path, tarfile)

        self.set_output(output)
        self.set_error(error)


MozillaTarballAction.moztar = MozillaTarballAction(category="Other actions",
                                                   title="Download tarball")
