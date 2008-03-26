#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2007 Zuza Software Foundation
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

"""Module to provide a cache of statistics in a database.

@organization: Zuza Software Foundation
@copyright: 2007 Zuza Software Foundation
@license: U{GPL <http://www.fsf.org/licensing/licenses/gpl.html>}
"""

from translate import __version__ as toolkitversion
from translate.storage import factory
from translate.misc.multistring import multistring
from translate.lang.common import Common

try:
    from sqlite3 import dbapi2
except ImportError:
    from pysqlite2 import dbapi2
import os.path
import re
import sys

kdepluralre = re.compile("^_n: ")
brtagre = re.compile("<br\s*?/?>")
xmltagre = re.compile("<[^>]+>")
numberre = re.compile("\\D\\.\\D")

state_strings = {0: "untranslated", 1: "translated", 2: "fuzzy"}

def wordcount(string):
    # TODO: po class should understand KDE style plurals
    string = kdepluralre.sub("", string)
    string = brtagre.sub("\n", string)
    string = xmltagre.sub("", string)
    string = numberre.sub(" ", string)
    #TODO: This should still use the correct language to count in the target 
    #language
    return len(Common.words(string))

def wordsinunit(unit):
    """Counts the words in the unit's source and target, taking plurals into 
    account. The target words are only counted if the unit is translated."""
    (sourcewords, targetwords) = (0, 0)
    if isinstance(unit.source, multistring):
        sourcestrings = unit.source.strings
    else:
        sourcestrings = [unit.source or ""]
    for s in sourcestrings:
        sourcewords += wordcount(s)
    if not unit.istranslated():
        return sourcewords, targetwords
    if isinstance(unit.target, multistring):
        targetstrings = unit.target.strings
    else:
        targetstrings = [unit.target or ""]
    for s in targetstrings:
        targetwords += wordcount(s)
    return sourcewords, targetwords

def statefordb(unit):
    """Returns the numeric database state for the unit."""
    if unit.istranslated():
        return 1
    if unit.isfuzzy() and unit.target:
        return 2
    return 0

def emptystats():
    """Returns a dictionary with all statistics initalised to 0."""
    stats = {}
    for state in ["total", "translated", "fuzzy", "untranslated", "review"]:
        stats[state] = 0
        stats[state + "sourcewords"] = 0
        stats[state + "targetwords"] = 0
    return stats

def suggestioninfo(filename):
    """Provides the filename of the associated file containing suggestions and 
    its mtime, if it exists."""
    root, ext = os.path.splitext(filename)
    suggestion_filename = None
    suggestion_mtime = -1
    if ext == os.path.extsep + "po":
        # For a PO file there might be an associated file with suggested
        # translations. If either file changed, we want to regenerate the
        # statistics.
        suggestion_filename = filename + os.path.extsep + 'pending'
        if not os.path.exists(suggestion_filename):
            suggestion_filename = None
        else:
            suggestion_mtime = os.path.getmtime(suggestion_filename)
    return suggestion_filename, suggestion_mtime

class StatsCache(object):
    """An object instantiated as a singleton for each statsfile that provides 
    access to the database cache from a pool of StatsCache objects."""
    caches = {}
    defaultfile = None
    con = None
    """This cache's connection"""
    cur = None
    """The current cursor"""

    def __new__(cls, statsfile=None):
        if not statsfile:
            if not cls.defaultfile:
                userdir = os.path.expanduser("~")
                cachedir = None
                if os.name == "nt":
                    cachedir = os.path.join(userdir, "Translate Toolkit")
                else:
                    cachedir = os.path.join(userdir, ".translate_toolkit")
                if not os.path.exists(cachedir):
                    os.mkdir(cachedir)
                cls.defaultfile = os.path.realpath(os.path.join(cachedir, "stats.db"))
            statsfile = cls.defaultfile
        else:
            statsfile = os.path.realpath(statsfile)
        # First see if a cache for this file already exists:
        if statsfile in cls.caches:
            return cls.caches[statsfile]
        # No existing cache. Let's build a new one and keep a copy
        cache = cls.caches[statsfile] = object.__new__(cls)
        cache.con = dbapi2.connect(statsfile)
        cache.cur = cache.con.cursor()
        cache.create()
        return cache

    def create(self):
        """Create all tables and indexes."""
        self.cur.execute("""CREATE TABLE IF NOT EXISTS files(
            fileid INTEGER PRIMARY KEY AUTOINCREMENT,
            path VARCHAR NOT NULL UNIQUE,
            mtime INTEGER NOT NULL,
            toolkitbuild INTEGER NOT NULL);""")

        self.cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS filepathindex
            ON files (path);""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS units(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unitid VARCHAR NOT NULL,
            fileid INTEGER NOT NULL,
            unitindex INTEGER NOT NULL,
            source VARCHAR NOT NULL,
            target VARCHAR,
            state INTEGER,
            sourcewords INTEGER,
            targetwords INTEGER);""")
        
        self.cur.execute("""CREATE INDEX IF NOT EXISTS fileidindex
            ON units(fileid);""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS checkerconfigs(
            configid INTEGER PRIMARY KEY AUTOINCREMENT,
            config VARCHAR);""")

        self.cur.execute("""CREATE INDEX IF NOT EXISTS configindex
            ON checkerconfigs(config);""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS uniterrors(
            errorid INTEGER PRIMARY KEY AUTOINCREMENT,
            unitindex INTEGER NOT NULL,
            fileid INTEGER NOT NULL,
            configid INTEGER NOT NULL,
            name VARCHAR NOT NULL,
            message VARCHAR);""")

        self.cur.execute("""CREATE INDEX IF NOT EXISTS uniterrorindex
            ON uniterrors(fileid, configid);""")
        
        self.con.commit()

    def _getstoredfileid(self, filename, optmtime=-1, checkmtime=True):
        """Attempt to find the fileid of the given file, if it hasn't been
        updated since the last record update.

        None is returned if either the file's record is not found, or if it is
        not up to date.

        @param filename: the filename to retrieve the id for
        @param optmtime: an optional mtime to consider in addition to the mtime of
        the given file
        @rtype: String or None
        """
        realpath = os.path.realpath(filename)
        self.cur.execute("""SELECT fileid, mtime FROM files 
                WHERE path=?;""", (realpath,))
        filerow = self.cur.fetchone()
        mtime = max(optmtime, os.path.getmtime(realpath))
        if checkmtime:
            if not filerow or filerow[1] != mtime:
                return None
        if filerow:
            fileid = filerow[0]
            if not checkmtime:
                # Update the mtime of the file
                self.cur.execute("""UPDATE files 
                        SET mtime=? 
                        WHERE fileid=?;""", (mtime, fileid))
            return fileid
        return None

    def _getstoredcheckerconfig(self, checker):
        """See if this checker configuration has been used before."""
        config = str(checker.config.__dict__)
        self.cur.execute("""SELECT configid, config FROM checkerconfigs WHERE 
            config=?;""", (config,))
        configrow = self.cur.fetchone()
        if not configrow or configrow[1] != config:
            return None
        else:
            return configrow[0]

    def _cacheunitstats(self, units, fileid, unitindex=None):
        """Cache the statistics for the supplied unit(s)."""
        unitvalues = []
        for index, unit in enumerate(units):
            if unit.istranslatable():
                sourcewords, targetwords = wordsinunit(unit)
                if unitindex:
                    index = unitindex
                # what about plurals in .source and .target?
                unitvalues.append((unit.getid(), fileid, index, \
                                unit.source, unit.target, \
                                sourcewords, targetwords, \
                                statefordb(unit)))
        # XXX: executemany is non-standard
        self.cur.executemany("""INSERT INTO units
            (unitid, fileid, unitindex, source, target, sourcewords, targetwords, state) 
            values (?, ?, ?, ?, ?, ?, ?, ?);""",
            unitvalues)
        self.con.commit()
        if unitindex:
            return state_strings[statefordb(units[0])]
        return ""

    def cachestore(self, store):
        """Calculates and caches the statistics of the given store 
        unconditionally."""
        realpath = os.path.realpath(store.filename)
        mtime = os.path.getmtime(realpath)
        self.cur.execute("""DELETE FROM files WHERE
            path=?;""", (realpath,))
        self.cur.execute("""INSERT INTO files 
            (fileid, path, mtime, toolkitbuild) values (NULL, ?, ?, ?);""", 
            (realpath, mtime, toolkitversion.build))
        fileid = self.cur.lastrowid
        self.cur.execute("""DELETE FROM units WHERE
            fileid=?""", (fileid,))
        self._cacheunitstats(store.units, fileid)
        return fileid

    def directorytotals(self, dirname):
        """Retrieves the stored statistics for a given directory, all summed.
        
        Note that this does not check for mtimes or the presence of files."""
        realpath = os.path.realpath(dirname)
        self.cur.execute("""SELECT
            state,
            count(unitid) as total,
            sum(sourcewords) as sourcewords,
            sum(targetwords) as targetwords
            FROM units WHERE fileid IN
                (SELECT fileid from files
                WHERE substr(path, 0, ?)=?)
            GROUP BY state;""", (len(realpath), realpath))
        totals = emptystats()
        return self.cur.fetchall()

    def filetotals(self, filename):
        """Retrieves the statistics for the given file if possible, otherwise 
        delegates to cachestore()."""
        fileid = self._getstoredfileid(filename)
        if not fileid:
            try:
                store = factory.getobject(filename)
                fileid = self.cachestore(store)
            except ValueError, e:
                print >> sys.stderr, str(e)
                return {}

        self.cur.execute("""SELECT 
            state,
            count(unitid) as total,
            sum(sourcewords) as sourcewords,
            sum(targetwords) as targetwords
            FROM units WHERE fileid=?
            GROUP BY state;""", (fileid,))
        values = self.cur.fetchall()

        totals = emptystats()
        for stateset in values:
            state = state_strings[stateset[0]]          # state
            totals[state] = stateset[1] or 0            # total
            totals[state + "sourcewords"] = stateset[2] # sourcewords
            totals[state + "targetwords"] = stateset[3] # targetwords
        totals["total"] = totals["untranslated"] + totals["translated"] + totals["fuzzy"]
        totals["totalsourcewords"] = totals["untranslatedsourcewords"] + \
                totals["translatedsourcewords"] + \
                totals["fuzzysourcewords"]
        return totals

    def _cacheunitschecks(self, units, fileid, configid, checker, unitindex=None):
        """Helper method for cachestorechecks() and recacheunit()"""
        # We always want to store one dummy error to know that we have actually
        # run the checks on this file with the current checker configuration
        dummy = (-1, fileid, configid, "noerror", "")
        unitvalues = [dummy]
        # if we are doing a single unit, we want to return the checknames
        errornames = []
        for index, unit in enumerate(units):
            if unit.istranslatable():
                # Correctly assign the unitindex
                if unitindex:
                    index = unitindex
                failures = checker.run_filters(unit)
                for checkname, checkmessage in failures.iteritems():
                    unitvalues.append((index, fileid, configid, checkname, checkmessage))
                    errornames.append("check-" + checkname)
        checker.setsuggestionstore(None)


        if unitindex:
            # We are only updating a single unit, so we don't want to add an 
            # extra noerror-entry
            unitvalues.remove(dummy)
            errornames.append("total")

        # XXX: executemany is non-standard
        self.cur.executemany("""INSERT INTO uniterrors
            (unitindex, fileid, configid, name, message) 
            values (?, ?, ?, ?, ?);""",
            unitvalues)
        self.con.commit()
        return errornames

    def cachestorechecks(self, fileid, store, checker, configid):
        """Calculates and caches the error statistics of the given store 
        unconditionally."""
        # Let's purge all previous failures because they will probably just
        # fill up the database without much use.
        self.cur.execute("""DELETE FROM uniterrors WHERE
            fileid=?;""", (fileid,))
        self._cacheunitschecks(store.units, fileid, configid, checker)
        return fileid

    def recacheunit(self, filename, checker, unit):
        """Recalculate all information for a specific unit. This is necessary
        for updating all statistics when a translation of a unit took place, 
        for example.
        
        This method assumes that everything was up to date before (file totals,
        checks, checker config, etc."""
        suggestion_filename, suggestion_mtime = suggestioninfo(filename)
        fileid = self._getstoredfileid(filename, suggestion_mtime, checkmtime=False)
        configid = self._getstoredcheckerconfig(checker)
        unitid = unit.getid()
        # get the unit index
        self.cur.execute("""SELECT unitindex FROM units WHERE
            fileid=? AND unitid=?;""", (fileid, unitid))
        unitindex = self.cur.fetchone()[0]
        self.cur.execute("""DELETE FROM units WHERE
            fileid=? AND unitid=?;""", (fileid, unitid))
        state = [self._cacheunitstats([unit], fileid, unitindex)]
        # remove the current errors
        self.cur.execute("""DELETE FROM uniterrors WHERE
            fileid=? AND unitindex=?;""", (fileid, unitindex))
        if suggestion_filename:
            checker.setsuggestionstore(factory.getobject(suggestion_filename, ignore=os.path.extsep+ 'pending'))
        state.extend(self._cacheunitschecks([unit], fileid, configid, checker, unitindex))
        return state

    def filechecks(self, filename, checker, store=None):
        """Retrieves the error statistics for the given file if possible, 
        otherwise delegates to cachestorechecks()."""
        suggestion_filename, suggestion_mtime = suggestioninfo(filename)
        fileid = self._getstoredfileid(filename, suggestion_mtime)
        configid = self._getstoredcheckerconfig(checker)
        try:
            if not fileid:
                store = store or factory.getobject(filename)
                fileid = self.cachestore(store)
            if not configid:
                self.cur.execute("""INSERT INTO checkerconfigs
                    (configid, config) values (NULL, ?);""", 
                    (str(checker.config.__dict__),))
                configid = self.cur.lastrowid
        except ValueError, e:
            print >> sys.stderr, str(e)
            return {}

        def geterrors():
            self.cur.execute("""SELECT 
                name,
                unitindex
                FROM uniterrors WHERE fileid=? and configid=?
                ORDER BY unitindex;""", (fileid, configid))
            return self.cur.fetchall()

        values = geterrors()
        if not values:
            # This could happen if we haven't done the checks before, or we the
            # file changed, or we are using a different configuration
            store = store or factory.getobject(filename)
            if suggestion_filename:
                checker.setsuggestionstore(factory.getobject(suggestion_filename, ignore=os.path.extsep+ 'pending'))
            self.cachestorechecks(fileid, store, checker, configid)
            values = geterrors()

        errors = {}
        for value in values:
            if value[1] == -1:
                continue
            checkkey = 'check-' + value[0]      #value[0] is the error name
            if not checkkey in errors:
                errors[checkkey] = []
            errors[checkkey].append(value[1])   #value[1] is the unitindex

        return errors

    def filestats(self, filename, checker, store=None):
        """complete stats"""
        stats = {"total": [], "translated": [], "fuzzy": [], "untranslated": []}

        stats.update(self.filechecks(filename, checker, store))
        fileid = self._getstoredfileid(filename)

        self.cur.execute("""SELECT 
            state,
            unitindex
            FROM units WHERE fileid=?
            ORDER BY unitindex;""", (fileid,))

        values = self.cur.fetchall()
        for value in values:
            stats[state_strings[value[0]]].append(value[1])
            stats["total"].append(value[1])

        return stats
