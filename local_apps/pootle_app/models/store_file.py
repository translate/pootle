#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2006 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""manages a translation file and its associated files"""

import time
import os
import bisect
import weakref
import logging

from django.conf import settings

from translate.storage import base
from translate.storage import po
from translate.storage.poheader import tzstring
from translate.storage import xliff
from translate.storage import factory
from translate.filters import checks
from translate.misc.multistring import multistring

from pootle_app.lib import util, statistics, lru_cache
from pootle_app.lib.legacy.jToolkit import timecache, glock
from pootle_app import __version__

_UNIT_CHECKER = checks.UnitChecker()

suggestion_source_index = weakref.WeakKeyDictionary()


class pootleassigns:
    """this represents the assignments for a file"""

    def __init__(self, basefile):
        """constructs assignments object for the given file"""

        # TODO: try and remove circular references between basefile
        # and this class
        self.basefile = basefile
        self.assignsfilename = self.basefile.filename + os.extsep + 'assigns'
        self.getassigns()

    def getassigns(self):
        """reads the assigns if neccessary or returns them from the
        cache"""

        if os.path.exists(self.assignsfilename):
            self.assigns = self.readassigns()
        else:
            self.assigns = {}
        return self.assigns

    def readassigns(self):
        """reads the assigns from the associated assigns file,
        returning the assigns the format is a number of lines
        consisting of username: action: itemranges where itemranges is
        a comma-separated list of item numbers or itemranges like 3-5
        e.g.  pootlewizz: review: 2-99,101"""

        assignsmtime = statistics.getmodtime(self.assignsfilename)
        if assignsmtime == getattr(self, 'assignsmtime', None):
            return
        assignsfile = open(self.assignsfilename, 'r')
        assignsstring = assignsfile.read()
        assignsfile.close()
        poassigns = {}
        itemcount = len(getattr(self, 'stats', {}).get('total', []))
        for line in assignsstring.split('\n'):
            if not line.strip():
                continue
            if not line.count(':') == 2:
                loggin.error('invalid assigns line in %s: %r' \
                             % (self.assignsfilename, line))
                continue
            (username, action, itemranges) = line.split(':', 2)
            (username, action) = (username.strip().decode('utf-8'),
                                  action.strip().decode('utf-8'))
            if not username in poassigns:
                poassigns[username] = {}
            userassigns = poassigns[username]
            if not action in userassigns:
                userassigns[action] = []
            items = userassigns[action]
            for itemrange in itemranges.split(','):
                if '-' in itemrange:
                    if not itemrange.count('-') == 1:
                        logging.error('invalid assigns range in %s: %r (from line %r)',
                                      self.assignsfilename, itemrange, line)
                        continue
                    (itemstart, itemstop) = [int(item.strip()) for item in
                            itemrange.split('-', 1)]
                    items.extend(range(itemstart, itemstop + 1))
                else:
                    item = int(itemrange.strip())
                    items.append(item)
            if itemcount:
                items = [item for item in items if 0 <= item < itemcount]
            userassigns[action] = items
        return poassigns

    def assignto(self, item, username, action):
        """assigns the item to the given username for the given action"""

        userassigns = self.assigns.setdefault(username, {})
        items = userassigns.setdefault(action, [])
        if item not in items:
            items.append(item)
        self.saveassigns()

    def unassign(self, item, username=None, action=None):
        """removes assignments of the item to the given username (or
        all users) for the given action (or all actions)"""

        if username is None:
            usernames = self.assigns.keys()
        else:
            usernames = [username]
        for username in usernames:
            userassigns = self.assigns.setdefault(username, {})
            if action is None:
                itemlist = [userassigns.get(action, []) for action in
                            userassigns]
            else:
                itemlist = [userassigns.get(action, [])]
            for items in itemlist:
                if item in items:
                    items.remove(item)
        self.saveassigns()

    def saveassigns(self):
        """saves the current assigns to file"""

        # assumes self.assigns is up to date
        assignstrings = []
        usernames = self.assigns.keys()
        usernames.sort()
        for username in usernames:
            actions = self.assigns[username].keys()
            actions.sort()
            for action in actions:
                items = self.assigns[username][action]
                items.sort()
                if items:
                    lastitem = None
                    rangestart = None
                    assignstring = '%s: %s: ' % (username.encode('utf-8'),
                            action.encode('utf-8'))
                    for item in items:
                        if item - 1 == lastitem:
                            if rangestart is None:
                                rangestart = lastitem
                        else:
                            if rangestart is not None:
                                assignstring += '-%d' % lastitem
                                rangestart = None
                            if lastitem is None:
                                assignstring += '%d' % item
                            else:
                                assignstring += ',%d' % item
                        lastitem = item
                    if rangestart is not None:
                        assignstring += '-%d' % lastitem
                    assignstrings.append(assignstring + '\n')
        assignsfile = open(self.assignsfilename, 'w')
        assignsfile.writelines(assignstrings)
        assignsfile.close()

    def getunassigned(self, action=None):
        """gets all strings that are unassigned (for the given action
        if given)"""

        unassigneditems = range(0, self.basefile.statistics.getitemslen())
        self.assigns = self.getassigns()
        for username in self.assigns:
            if action is not None:
                assigneditems = self.assigns[username].get(action, [])
            else:
                assigneditems = []
                for (action, actionitems) in self.assigns[username].iteritems():
                    assigneditems += actionitems
            unassigneditems = [item for item in unassigneditems if item
                                not in assigneditems]
        return unassigneditems

    def finditems(self, search):
        """returns items that match the .assignedto and/or
        .assignedaction criteria in the searchobject"""

        # search.assignedto == [None] means assigned to nobody
        if search.assignedto == [None]:
            assignitems = self.getunassigned(search.assignedaction)
        else:
            # filter based on assign criteria
            assigns = self.getassigns()
            if search.assignedto:
                usernames = [search.assignedto]
            else:
                usernames = assigns.iterkeys()
            assignitems = []
            for username in usernames:
                if search.assignedaction:
                    actionitems = assigns[username].get(search.assignedaction,
                            [])
                    assignitems.extend(actionitems)
                else:
                    for actionitems in assigns[username].itervalues():
                        assignitems.extend(actionitems)
        return assignitems


def make_class(base_class):
    class store_file(base_class):
        """this represents a pootle-managed file and its associated
        files"""

        x_generator = 'Pootle %s' % __version__.sver

        def __init__(self, translation_project=None, pofilename=None):
            if pofilename:
                self.__class__.__bases__ = (factory.getclass(pofilename), )
            super(store_file, self).__init__()
            self.pofilename = pofilename
            self.filename = self.pofilename
            if translation_project is None:
                self.checker = None
                self.languagecode = 'en'
                self.translation_project_id = -1
            else:
                self.checker = translation_project.checker
                self.languagecode = translation_project.language.code
                self.translation_project_id = translation_project.id

            self.lockedfile = LockedFile(self.filename)
            # we delay parsing until it is required
            self.pomtime = None
            self.assigns = None

            self.pendingfilename = self.filename + os.extsep + 'pending'
            self.pendingfile = None
            self.pomtime = self.lockedfile.readmodtime()
            self.statistics = statistics.pootlestatistics(self)
            self.tmfilename = self.filename + os.extsep + 'tm'
            # we delay parsing until it is required
            self.pomtime = None
            self.tracker = timecache.timecache(20 * 60)

        @util.lazy('_id_index')
        def _get_id_index(self):
            return dict((unit.getid(), unit) for unit in self.units)

        id_index = property(_get_id_index)

        def parsestring(cls, storestring):
            newstore = cls()
            newstore.parse(storestring)
            return newstore

        parsestring = classmethod(parsestring)

        def parsefile(cls, storefile):
            """Reads the given file (or opens the given filename) and
            parses back to an object"""

            if isinstance(storefile, basestring):
                storefile = open(storefile, 'r')
            if 'r' in getattr(storefile, 'mode', 'r'):
                storestring = storefile.read()
            else:
                storestring = ''
            return cls.parsestring(storestring)

        parsefile = classmethod(parsefile)


        def track(self, item, message):
            """sets the tracker message for the given item"""

            self.tracker[item] = message

        def readpofile(self):
            """reads and parses the main file"""

            # make sure encoding is reset so it is read from the file
            self.encoding = None
            self.units = []
            if hasattr(self, '_total'):
                del self._total
            (pomtime, filecontents) = self.lockedfile.getcontents()
            # note: we rely on this not resetting the filename, which
            # we set earlier, when given a string
            self.parse(filecontents)
            self.pomtime = pomtime

        def savepofile(self):
            """saves changes to the main file to disk..."""

            output = str(self)
            # We have probably invalidated the totals array, so delete it.
            if hasattr(self, '_total'):
                del self._total
            self.pomtime = self.lockedfile.writecontents(output)

        def pofreshen(self):
            """makes sure we have a freshly parsed pofile

            @return: True if the file was freshened, False otherwise"""

            try:
                if self.pomtime != self.lockedfile.readmodtime():
                    self.readpofile()
                    return True
            except OSError, e:
                # If this exception is not triggered by a bad symlink,
                # then we have a missing file on our hands...
                if not os.path.islink(self.filename):
                    # ...and thus we rescan our files to get rid of
                    # the missing filename
                    from pootle_app.project_tree import scan_translation_project_files
                    from pootle_app.models.translation_project import TranslationProject
                    scan_translation_project_files(TranslationProject.objects.get(id=self.translation_project_id))
                else:
                    logging.error('%s is a broken symlink', self.filename)
            return False

        def getoutput(self):
            """returns pofile output"""

            self.pofreshen()
            return super(store_file, self).getoutput()


        def getassigns(self):
            if self.assigns is None:
                self.assigns = pootleassigns(self)
            return self.assigns

    return store_file


_store_file_classes = {}

# We want to extend the functionality of translation stores with some
# Pootle-specific functionality, but we still want them to act like
# translation stores. The clean way to do this, is to store a
# reference to a translation store inside a "store_file" class and to
# delegate if needed to the store. This was done initially through
# __getattr__ and __setattr__, although it proved to be rather slow
# (which made a difference for large sets of translation files). This
# is now achieved through inheritance. When we have to load a
# translation file, we get hold of its corresponding translation store
# class. Then we see whether there is a class which contains
# store_file functionality and which derives from the translation
# store class. If there isn't we invoke make_class to create such a
# class. Then we return an instance of this class to the user.


def store_file(project=None, store_filename=None):
    klass = po.pofile
    if store_filename != None:
        klass = factory.getclass(store_filename)
    if klass not in _store_file_classes:
        _store_file_classes[klass] = make_class(klass)
    return _store_file_classes[klass](project, store_filename)


class Search:
    """an object containing all the searching information"""

    def __init__(self, dirfilter=None, matchnames=[], assignedto=None,
                 assignedaction=None, searchtext=None, searchfields=None):
        if searchfields is None:
            searchfields = ['source', 'target']
        self.dirfilter = dirfilter
        self.matchnames = matchnames
        self.assignedto = assignedto
        self.assignedaction = assignedaction
        self.searchtext = searchtext
        self.searchfields = searchfields

    def copy(self):
        """returns a copy of this search"""

        return Search(
            self.dirfilter,
            self.matchnames,
            self.assignedto,
            self.assignedaction,
            self.searchtext,
            self.searchfields,
            )


# ###############################################################################

store_files = lru_cache.LRUCache(settings.STORE_LRU_CACHE_SIZE, lambda project_filename: \
                                      store_file(project_filename[0], project_filename[1]))



# ###############################################################################


def set_translation_project(store_files, translation_project):
    for store_file in store_files:
        store_file._with_store_file_ref_count = getattr(store_file,
                '_with_store_file_ref_count', 0) + 1
        store_file.translation_project = translation_project


def freshen_files(store_files, translation_project):
    for store_file in store_files:
        store_file.pofreshen()
        # Set the mtime of the TranslationProject to the most recent
        # mtime of a store loaded for this TranslationProject.
        translation_project.pomtime = max(translation_project.pomtime,
                store_file.pomtime)


def unset_translation_project(store_files):
    for store_file in store_files:
        store_file._with_store_file_ref_count -= 1
        if store_file._with_store_file_ref_count == 0:
            del store_file._with_store_file_ref_count
            del store_file.translation_project



def set_stores(store_files, stores):
    for (store_file, store) in zip(store_files, stores):
        store_file._with_store_ref_count = getattr(store_file,
                '_with_store_ref_count', 0) + 1
        store_file.store = store


def unset_stores(store_files):
    for store_file in store_files:
        store_file._with_store_ref_count -= 1
        if store_file._with_store_ref_count == 0:
            del store_file._with_store_ref_count
            del store_file.store



# ###############################################################################


def set_store_file(translation_project, filename, store_file):

    def do_set(store_files):
        store_files[filename] = store_files

    return with_store_file_cache(do_set)

