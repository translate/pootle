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
from pootle_app.models.permissions import check_permission

MOZL10N = "mozilla-l10n"
AURORA = "mozilla-aurora"
PROJECTS = ("firefox", "mobile")


def getLogger(name):  # pylint: disable=C0103
    """Return a logger with a new method: debug_exception()

    :param name: logger name (typically __name__)
    :returns: logging.getLogger(name) with debug_exception method
    :rtype: logging.Logger
    """
    import types

    _logger = logging.getLogger(name)

    # Monkey-patch the instance with additional method rather than create a
    # subclass of Logger because the only way to create instances is via
    # logging module factory function getLogger(), which lacks any way to
    # create a subclass instead.  The Logger class itself could be monkey-
    # patched with the additional method, but that seems too far-reaching,
    # since it would apply to all Loggers everywhere.

    def debug_exception(self, *args, **kwargs):
        """Log ERROR, with exception traceback only if logging at DEBUG level.

        This is useful when exceptions are probably not caused by programming
        errors, but rather deployment ones (filesystem permissions or missing
        files) - in most cases the function traceback is just a lot of noise
        confusing the administrator who deployed the system, and you don't want
        to show it.  When you do need it, just set the logging level to DEBUG.

        """
        e = 'exc_info'
        if e not in kwargs:
            kwargs[e] = self.getEffectiveLevel() == logging.DEBUG
        self.error(*args, **kwargs)

    _logger.debug_exception = types.MethodType(debug_exception, _logger)
    return _logger

logger = getLogger(__name__)


@contextmanager
def tempdir():
    """Context manager for creating and deleting a temporary directory."""
    tmpdir = mkdtemp()
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir)


def get_version(vc_root):
    """Get Mozilla version from browser (since mobile has no version.txt)

    :param vc_root:Pootle VCS_DIRECTORY setting
    :type vc_root:str
    :returns: Mozilla Firefox version string
    :rtype: str
    """
    vfile = os.path.join(vc_root, AURORA, 'browser', 'config', 'version.txt')
    try:
        with open(vfile) as vfh:
            version = vfh.readline()
    except IOError:
        logger.exception("Unable to get version from %s", vfile)
        return "aurora"

    return version.strip()


def get_phases(srcdir, phasedir, workdir, language, project):
    """Create repository-layout tree of PO files from translations.

    The srcdir should be compatible with Pootle translations layout
    (phased); phasedir is mozilla-l10n layout and used only for getting
    phase file list.  The workdir will also be compatible with mozilla-l10n
    layout but holding only translations in post-phase-gathered tree.

    (Re)raises IOError, OSError, and/or shutil.Error from open, os.makedirs,
    and/or shutil.copyfile

    :param phasedir: mozilla-l10n directory with phase configuration
    :type phasedir: str
    :param srcdir: Directory for translations (in phase-scattered locations)
    :type srcdir: str
    :param workdir: Output directory for post-phase-gathered tree
    :type workdir: str
    :param language: Language code (e.g. xx_XX)
    :type language: str
    :param project: Project code (e.g. firefox or mobile)
    :type project: str
    :raises IOError:
    :raises OSError:
    :raises shutil.Error:
    """

    phasefile = os.path.join(phasedir, MOZL10N, ".ttk", project,
                             project + ".phaselist")
    tdirs = set()
    try:
        with open(phasefile) as pfile:
            for phase in [line.strip().split() for line in pfile]:
                path = phase[1]
                if path.startswith('./'):
                    path = path[2:]
                source = os.path.join(srcdir, project, language, phase[0],
                                      path)
                target = os.path.join(workdir, language, path)
                tdir = target[:target.rfind(os.sep)]
                if tdir not in tdirs:
                    logger.debug("creating '%s' directory", tdir)
                    try:
                        os.makedirs(tdir)
                    except OSError, e:
                        if e.errno == errno.EEXIST and os.path.isdir(tdir):
                            pass
                        else:
                            raise
                    while tdir:
                        tdirs.add(tdir)
                        tdir = tdir[:tdir.rfind(os.sep)]
                logger.debug("copying '%s' to '%s'", source, target)
                try:
                    shutil.copyfile(source, target)
                except (shutil.Error, IOError):
                    logger.exception("Cannot update %s", target)
                    raise
    except IOError:
        logger.exception("Cannot get phases from %s", phasefile)
        raise


def merge_po2moz(templates, translations, output, language, project):
    """Run po2moz to merge templates and translations into output directory

    The templates directory should be compatible with mozilla-l10n layout,
    translation directory as well (i.e. post-phasefile gatherin) - the
    output directory will be appropriate for tarball generation.

    May raise IOError or OSError from po2moz operation.

    :param templates: Directory for en-US templates
    :type templates: str
    :param translations: Directory for translations
    :type translations: str
    :param output: Output directory for merged localization
    :type output: str
    :param language: Language code (e.g. xx_XX)
    :type language: str
    :param project: Project code (e.g. firefox or mobile)
    :type project: str
    :raises: IOError
    :raises: OSError

    """
    excludes = []
    if project == 'firefox':
        excludes.extend(["other-licenses/branding/firefox",
                         "extensions/reporter"])

    excludes.extend(['.git', '.hg', '.hgtags', 'obsolete', 'editor',
                     'mail', 'thunderbird', 'chat', '*~'])

    po2moz.main(['--progress=none', '-l', language,
                '-t', os.path.join(templates, MOZL10N, 'templates-en-US'),
                '-i', os.path.join(translations, language),
                '-o', os.path.join(output, language)] +
                # generate additional --exclude FOO arguments
                [opt or arg for arg in excludes for opt in ('--exclude', 0)])

class MozillaAction(TranslationProjectAction):
    """Base class for common functionality of Mozilla actions."""

    def is_active(self, request):
        project = request.translation_project.project.code
        if project not in PROJECTS:
            return False
        else:
            return super(MozillaAction, self).is_active(request)

class MozillaTarballAction(DownloadAction, MozillaAction):
    """Download Mozilla language properties tarball"""

    def __init__(self, **kwargs):
        super(MozillaTarballAction, self).__init__(**kwargs)

    def is_active(self, request):
        if not check_permission('administrate', request):
            return False
        else:
            return super(MozillaTarballAction, self).is_active(request)

    def run(self, path, root, tpdir,  # pylint: disable=R0913
            language, project, vc_root, **kwargs):
        """Generate a Mozilla language properties tarball"""

        with tempdir() as podir:
            try:
                get_phases(root, vc_root, podir, language, project)
            except (EnvironmentError, shutil.Error), e:
                logger.debug_exception(e)
                self.set_error(e)
                return

            process = subprocess.Popen(["git", "rev-parse",
                                        "--short", "HEAD"],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       cwd=os.path.join(vc_root, MOZL10N))
            output = process.communicate()[0]
            if not process.returncode == 0 or not output:
                output = "0000000"

            with tempdir() as tardir:
                try:
                    merge_po2moz(vc_root, podir, tardir, language, project)
                except EnvironmentError, e:
                    logger.debug_exception(e)
                    self.set_error(e)
                    return

                tarfile = '-'.join([language, get_version(vc_root),
                                    datetime.utcnow().strftime("%Y%m%dT%H%M"),
                                    output.strip()])
                tarfile = os.path.join(root, tpdir,
                                       '.'.join([tarfile, 'tar', 'bz2']))

                process = subprocess.Popen(['tar', '-cjf', tarfile, language],
                                           universal_newlines=True,
                                           close_fds=(os.name != 'nt'),
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, cwd=tardir)
                (output, error) = process.communicate()
                if process.returncode > 0:
                    error += (" [tar exited with status %d]\n" %
                              process.returncode)
                elif process.returncode < 0:
                    error += (" [tar killed by signal %d]\n" %
                              -process.returncode)
                else:
                    error += self.set_download_file(path, tarfile)

        self.set_output(output)
        self.set_error(error)


MozillaTarballAction.moztar = MozillaTarballAction(category="Mozilla",
                                                   title="Download tarball")
