# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from dirsync.syncer import Syncer as BaseSyncer


class Syncer(BaseSyncer):
    """Overridden due to noisy logging in dirsync.Syncer"""

    pkg_name = "dirsync"

    def log(self, msg, debug=False):
        if debug:
            self.logger.debug(
                "[%s] %s",
                self.pkg_name, msg)
        else:
            self.logger.info(
                "[%s] %s",
                self.pkg_name, msg)

    def report(self):
        """Print report of work at the end"""

        # We need only the first 4 significant digits
        tt = (str(self._endtime - self._starttime))[:4]

        self.log(
            '%d directories parsed, %d files copied' %
            (self._numdirs, self._numfiles),
            debug=not self._numfiles)
        if self._numdelfiles:
            self.log('%d files were purged.' % self._numdelfiles)
        if self._numdeldirs:
            self.log('%d directories were purged.' % self._numdeldirs)
        if self._numnewdirs:
            self.log('%d directories were created.' % self._numnewdirs)
        if self._numupdates:
            self.log('%d files were updated by timestamp.' % self._numupdates)

        # Failure stats
        if self._numcopyfld:
            self.log('there were errors in copying %d files.'
                     % self._numcopyfld)
        if self._numdirsfld:
            self.log('there were errors in creating %d directories.'
                     % self._numdirsfld)
        if self._numupdsfld:
            self.log('there were errors in updating %d files.'
                     % self._numupdsfld)
        if self._numdeldfld:
            self.log('there were errors in purging %d directories.'
                     % self._numdeldfld)
        if self._numdelffld:
            self.log('there were errors in purging %d files.'
                     % self._numdelffld)

        self.log(
            '%s finished in %s seconds.'
            % (self.pkg_name, tt),
            debug=True)


def sync(sourcedir, targetdir, action, **options):

    copier = Syncer(sourcedir, targetdir, action, **options)
    copier.do_work()

    # print report at the end
    copier.report()

    return set(copier._changed).union(copier._added).union(copier._deleted)
