#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

import time
import os
import cStringIO
import gettext
import subprocess
import zipfile
import logging

from django.conf                   import settings
from django.db                     import models
from django.db.models.signals      import pre_delete, post_init, pre_save, post_save

from translate.filters import checks
from translate.convert import po2csv, po2xliff, xliff2po, po2ts, po2oo
from translate.tools   import pocompile, pogrep
from translate.search  import match, indexing
from translate.storage import statsdb, base, versioncontrol

from pootle_app.models.profile     import PootleProfile
from pootle_app.models.project     import Project
from pootle_app.models.language    import Language
from pootle_app.models.directory   import Directory
from pootle_store.models           import Store
from pootle_app                    import project_tree
from pootle_store.util             import relative_real_path, absolute_real_path
from pootle_app.models.permissions import PermissionError, check_permission
from pootle_app.lib                import statistics

from pootle.scripts                import hooks

class TranslationProjectNonDBState(object):
    def __init__(self, parent):
        self.parent = parent
        # terminology matcher
        self.termmatcher = None
        self.termmatchermtime = None
        self._indexing_enabled = True
        self._index_initialized = False

translation_project_non_db_state = {}

def create_translation_project(language, project):
    if project_tree.translation_project_should_exist(language, project):
        try:
            translation_project, created = TranslationProject.objects.get_or_create(language=language, project=project)
            project_tree.scan_translation_project_files(translation_project)
            return translation_project
        except OSError:
            return None
        except IndexError:
            return None

def scan_translation_projects():
    for language in Language.objects.all():
        for project in Project.objects.all():
            create_translation_project(language, project)

class TranslationProjectManager(models.Manager):
    def get_query_set(self, *args, **kwargs):
        return super(TranslationProjectManager, self).get_query_set(*args, **kwargs).select_related(depth=1)

class TranslationProject(models.Model):
    objects = TranslationProjectManager()

    index_directory  = ".translation_index"

    class Meta:
        unique_together = ('language', 'project')
        app_label = "pootle_app"

    language   = models.ForeignKey(Language, db_index=True)
    project    = models.ForeignKey(Project,  db_index=True)
    real_path  = models.FilePathField()
    directory  = models.ForeignKey(Directory)

    def __unicode__(self):
        return self.directory.pootle_path

    @classmethod
    def get_language_and_project_indices(cls):
      def add_to_list(dct, key, value):
        if key not in dct:
          dct[key] = []
        dct[key].append(value)

      language_index = {}
      project_index = {}
      for translation_project in TranslationProject.objects.select_related(depth=1).all():
        add_to_list(language_index, translation_project.language.code, translation_project)
        add_to_list(project_index,  translation_project.project.code,  translation_project)
      return language_index, project_index

    def _get_pootle_path(self):
        return self.directory.pootle_path
    pootle_path = property(_get_pootle_path)

    def _get_abs_real_path(self):
        return absolute_real_path(self.real_path)

    def _set_abs_real_path(self, value):
        self.real_path = relative_real_path(value)

    abs_real_path = property(_get_abs_real_path, _set_abs_real_path)

    def _get_treestyle(self):
        return self.project.get_treestyle()

    file_style = property(_get_treestyle)

    def _get_checker(self):
        checkerclasses = [checks.projectcheckers.get(self.project.checkstyle,
                                                     checks.StandardChecker),
                          checks.StandardUnitChecker]
        return checks.TeeChecker(checkerclasses=checkerclasses,
                                 errorhandler=self.filtererrorhandler,
                                 languagecode=self.language.code)

    checker = property(_get_checker)

    def filtererrorhandler(self, functionname, str1, str2, e):
        logging.error("error in filter %s: %r, %r, %s", functionname, str1, str2, e)
        return False

    def _get_non_db_state(self):
        if self.id not in translation_project_non_db_state:
            translation_project_non_db_state[self.id] = TranslationProjectNonDBState(self)
        return translation_project_non_db_state[self.id]

    non_db_state = property(_get_non_db_state)

    def getquickstats(self):
        if not self.is_template_project:
            return self.directory.getquickstats()
        else:
            #FIXME: Hackish return empty_stats to avoid messing up
            # with project and language stats
            empty_stats = {'fuzzy': 0,
                           'fuzzysourcewords': 0,
                           'review': 0,
                           'total': 0,
                           'totalsourcewords': 0,
                           'translated': 0,
                           'translatedsourcewords': 0,
                           'translatedtargetwords': 0,
                           'untranslated': 0,
                           'untranslatedsourcewords': 0}
            return empty_stats

    def _get_indexer(self):
        if self.non_db_state._indexing_enabled:
            try:
                indexer = self.make_indexer()
                if not self.non_db_state._index_initialized:
                    self.init_index(indexer)
                    self.non_db_state._index_initialized = True
                return indexer
            except Exception, e:
                logging.error("Could not intialize indexer for %s in %s: %s", self.project.code, self.language.code, str(e))
                self.non_db_state._indexing_enabled = False
                return None
        else:
            return None

    indexer = property(_get_indexer)

    def _has_index(self):
        return self.non_db_state._indexing_enabled and \
            (self.non_db_state._index_initialized or self.indexer != None)

    has_index = property(_has_index)

    def _get_profiles_with_interest(self):
        """returns all the users who registered for this language and
        project"""
        return PootleProfile.objects.filter(languages=self.language_id)

    profiles_with_interest = property(_get_profiles_with_interest)

    def _get_all_permission_sets(self):
        """gets all users that have rights defined for this project"""
        # Find all the Right objects which are associated with this translation project
        # select_related('profile__user') is an optimization to tell Django to select
        # the profile and their associated user objects along with our query (i.e. it
        # does a SQL join behind the scenes).
        return PermissionSet.objects.select_related('profile__user').filter(translation_project=self)

    all_permission_sets = property(_get_all_permission_sets)

    def _get_goals(self):
        return Goal.objects.filter(translation_project=self)

    goals = property(_get_goals)

    def get_profile_goals(self, profile):
        return Goal.objects.filter(profiles=profile, translation_project=self)

    def update_from_version_control(self):
        """updates project translation files from version control,
        retaining uncommitted translations"""

        stores = Store.objects.filter(pootle_path__startswith=self.directory.pootle_path)

        for store in stores:
            try:
                hooks.hook(self.project.code, "preupdate", store.file.path)
            except:
                # We should not hide the exception. At least log it.
                pass
            # keep a copy of working files in memory before updating
            working_copy = store.file.store

            try:
                logging.debug("updating %s from version control", store.file.path)
                versioncontrol.updatefile(store.file.path)
                store.file._delete_store_cache()
                store.mergefile(working_copy, "versionmerge", allownewstrings=False, obseletemissing=False)
            except Exception, e:
                #something wrong, file potentially modified, bail out
                #and replace with working copy
                logging.error("near fatal catastrophe, exception %s while updating %s from version control", e, store.file.path)
                working_copy.save()

            try:
                hooks.hook(self.project.code, "postupdate", store.file.path)
            except:
                pass

        project_tree.scan_translation_project_files(self)

    def runprojectscript(self, scriptdir, target, extraargs = []):
        currdir = os.getcwd()
        script = os.path.join(scriptdir, self.project.code)
        try:
            os.chdir(scriptdir)
            cmd = [script, target]
            cmd.extend(extraargs)
            subprocess.call(cmd)
        except:
            # We should not hide the exception, at least log it.
            pass # If something goes wrong, we just continue without worrying
        os.chdir(currdir)

    def updatepofile(self, request, store):
        """updates file from version control,
        retaining uncommitted translations"""
        if not check_permission("commit", request):
            raise PermissionError(_("You do not have rights to update from version control here"))

        try:
            hooks.hook(self.project.code, "preupdate", store.file.path)
        except:
            pass
        # keep a copy of working files in memory before updating
        working_stats = store.file.getquickstats()
        working_copy = store.file.store

        success = True
        try:
            logging.debug("updating %s from version control", store.file.path)
            versioncontrol.updatefile(store.file.path)
            store.file._delete_store_cache()
            remote_stats = store.file.getquickstats()
            store.mergefile(working_copy, "versionmerge", allownewstrings=False, obseletemissing=False)
            new_stats = store.file.getquickstats()
            request.user.message_set.create(message="Updated file: <em>%s</em>" % store.file.name)

            def stats_message(version, stats):
                return "%s: %d of %d messages translated (%d fuzzy)." % \
                              (version, stats["translated"], stats["total"], stats["fuzzy"])

            request.user.message_set.create(message=stats_message("working copy", working_stats))
            request.user.message_set.create(message=stats_message("remote copy", remote_stats))
            request.user.message_set.create(message=stats_message("merged copy", new_stats))
        except Exception, e:
            #something wrong, file potentially modified, bail out
            #and replace with working copy
            logging.error("near fatal catastrophe, exception %s while updating %s from version control", e, store.file.path)
            working_copy.save()
            success = False

        try:
            hooks.hook(self.project.code, "postupdate", store.file.path)
        except:
            pass

        project_tree.scan_translation_project_files(self)
        return success

    def commitpofile(self, request, store):
        """commits an individual PO file to version control"""
        if not check_permission("commit", request):
            raise PermissionError(_("You do not have rights to commit files here"))

        stats = store.file.getquickstats()
        statsstring = "%d of %d messages translated (%d fuzzy)." % \
                (stats["translated"], stats["total"], stats["fuzzy"])

        author = request.user.username
        message="Commit from %s by user %s. %s" % \
                  (settings.TITLE, author, statsstring)

        try:
            filestocommit = hooks.hook(self.project.code, "precommit", store.file.path, author=author, message=message)
        except ImportError:
            # Failed to import the hook - we're going to assume there just isn't a hook to
            # import.    That means we'll commit the original file.
            filestocommit = [store.file.path]

        success = True
        try:
            for file in filestocommit:
                versioncontrol.commitfile(file, message=message, author=author)
                request.user.message_set.create(message="Committed file: <em>%s</em>" % file)
        except Exception, e:
            logging.error("Failed to commit files: %s", e)
            request.user.message_set.create(message="Failed to commit file: %s" % e)
            success = False
        try:
            hooks.hook(self.project.code, "postcommit", store.file.path, success=success)
        except:
            # We should not hide the exception - makes development impossible
            pass
        return success


    def initialize(self):
        try:
            hooks.hook(self.project.code, "initialize", self.real_path, self.language.code)
            self.non_db_state.scanpofiles()
        except Exception, e:
            logging.error("Failed to initialize (%s): %s", self.language.code, e)

    def filtererrorhandler(self, functionname, str1, str2, e):
        logging.error("error in filter %s: %r, %r, %s", functionname, str1, str2, e)
        return False


    ##############################################################################################

    def get_archive(self, stores):
        """returns an archive of the given filenames"""
        try:
            # using zip command line is fast
            from tempfile import mkstemp
            # The temporary file below is opened and immediately closed for security reasons
            fd, tempzipfile = mkstemp(prefix='pootle', suffix='.zip')
            os.close(fd)
            os.system("cd %s ; zip -r - %s > %s" % (self.abs_real_path, " ".join(store.abs_real_path[len(self.abs_real_path)+1:] for store in stores), tempzipfile))
            filedata = open(tempzipfile, "r").read()
            if filedata:
                return filedata
        finally:
            if os.path.exists(tempzipfile):
                os.remove(tempzipfile)

        # but if it doesn't work, we can do it from python
        archivecontents = cStringIO.StringIO()
        archive = zipfile.ZipFile(archivecontents, 'w', zipfile.ZIP_DEFLATED)
        for store in stores:
            archive.write(store.abs_real_path.encode('utf-8'), store.abs_real_path[len(self.abs_real_path)+1:].encode('utf-8'))
        archive.close()
        return archivecontents.getvalue()

    def ootemplate(self):
        """Tests whether this project has an OpenOffice.org template SDF file in
        the templates directory."""
        projectdir = absolute_real_path(self.project.code)
        templatefilename = os.path.join(projectdir, "templates", "en-US.sdf")
        if os.path.exists(templatefilename):
            return templatefilename
        else:
            return None

    def getoo(self):
        """Returns an OpenOffice.org gsi file"""
        #TODO: implement caching
        templateoo = self.ootemplate()
        if templateoo is None:
            return
        outputoo = os.path.join(self.abs_real_path, self.languagecode + ".sdf")
        inputdir = self.abs_real_path
        po2oo.main(["-i%s"%inputdir, "-t%s"%templateoo, "-o%s"%outputoo, "-l%s"%self.languagecode, "--progress=none"])
        return file(os.path.join(self.abs_real_path, self.languagecode + ".sdf"), "r").read()

    ##############################################################################################

    def browsefiles(self, dirfilter=None, depth=None, maxdepth=None, includedirs=False, includefiles=True):
        """gets a list of pofilenames, optionally filtering with the parent directory"""
        if dirfilter is None:
            pofilenames = self.non_db_state.pofilenames
        else:
            if not dirfilter.endswith(os.path.sep) and not dirfilter.endswith(os.extsep + self.project.localfiletype):
                dirfilter += os.path.sep
            pofilenames = [pofilename for pofilename in self.non_db_state.pofilenames if pofilename.startswith(dirfilter)]
        if includedirs:
            podirs = {}
            for pofilename in pofilenames:
                dirname = os.path.dirname(pofilename)
                if not dirname:
                    continue
                podirs[dirname] = True
                while dirname:
                    dirname = os.path.dirname(dirname)
                    if dirname:
                        podirs[dirname] = True
            podirs = podirs.keys()
        else:
            podirs = []
        if not includefiles:
            pofilenames = []
        if maxdepth is not None:
            pofilenames = [pofilename for pofilename in pofilenames if pofilename.count(os.path.sep) <= maxdepth]
            podirs = [podir for podir in podirs if podir.count(os.path.sep) <= maxdepth]
        if depth is not None:
            pofilenames = [pofilename for pofilename in pofilenames if pofilename.count(os.path.sep) == depth]
            podirs = [podir for podir in podirs if podir.count(os.path.sep) == depth]
        return pofilenames + podirs

    ##############################################################################################

    def iterpofilenames(self, lastpofilename=None, includelast=False):
        """iterates through the pofilenames starting after the given pofilename"""
        if not lastpofilename:
            index = 0
        else:
            index = self.non_db_state.pofilenames.index(lastpofilename)
            if not includelast:
                index += 1
        while index < len(self.non_db_state.pofilenames):
            yield self.non_db_state.pofilenames[index]
            index += 1

    def make_indexer(self):
        """get an indexing object for this project

        Since we do not want to keep the indexing databases open for the lifetime of
        the TranslationProject (it is cached!), it may NOT be part of the Project object,
        but should be used via a short living local variable.
        """
        indexdir = os.path.join(self.abs_real_path, self.index_directory)
        index = indexing.get_indexer(indexdir)
        index.set_field_analyzers({
                        "pofilename": index.ANALYZER_EXACT,
                        "itemno": index.ANALYZER_EXACT,
                        "pomtime": index.ANALYZER_EXACT})
        return index

    def init_index(self, indexer):
        """initializes the search index"""
        for store in Store.objects.filter(pootle_path__startswith=self.directory.pootle_path):
            self.update_index(indexer, store, optimize=False)


    def update_index(self, indexer, store, items=None, optimize=True):
        """updates the index with the contents of pofilename (limit to items if given)

        There are three reasons for calling this function:
            1. creating a new instance of L{TranslationProject} (see L{initindex})
                    -> check if the index is up-to-date / rebuild the index if necessary
            2. translating a unit via the web interface
                    -> (re)index only the specified unit(s)

        The argument L{items} should be None for 1.

        known problems:
            1. This function should get called, when the po file changes externally.
                 WARNING: You have to stop the pootle server before manually changing
                 po files, if you want to keep the index database in sync.

        @param pofilename: absolute filename of the po file
        @type pofilename: str
        @param items: list of unit numbers within the po file OR None (=rebuild all)
        @type items: [int]
        @param optimize: should the indexing database be optimized afterwards
        @type optimize: bool
        """
        if indexer == None:
            return False
        # check if the pomtime in the index == the latest pomtime
        try:
            pomtime = statistics.getmodtime(store.file.path)
            pofilenamequery = indexer.make_query([("pofilename", store.pootle_path)], True)
            pomtimequery = indexer.make_query([("pomtime", str(pomtime))], True)
            gooditemsquery = indexer.make_query([pofilenamequery, pomtimequery], True)
            gooditemsnum = indexer.get_query_result(gooditemsquery).get_matches_count()
            # if there is at least one up-to-date indexing item, then the po file
            # was not changed externally -> no need to update the database
            if (gooditemsnum > 0) and (not items):
                # nothing to be done
                return
            elif items:
                # Update only specific items - usually single translation via the web
                # interface. All other items should still be up-to-date (even with an
                # older pomtime).
                # delete the relevant items from the database
                itemsquery = indexer.make_query([("itemno", str(itemno)) for itemno in items], False)
                indexer.delete_doc([pofilenamequery, itemsquery])
            else:
                # (items is None)
                # The po file is not indexed - or it was changed externally 
                # delete all items of this file
                indexer.delete_doc({"pofilename": store.pootle_path})
            if items is None:
                # rebuild the whole index
                items = range(store.file.getitemslen())
            addlist = []
            for itemno in items:
                unit = store.file.getitem(itemno)
                doc = {"pofilename": store.pootle_path, "pomtime": str(pomtime), "itemno": str(itemno)}
                if unit.hasplural():
                    orig = "\n".join(unit.source.strings)
                    trans = "\n".join(unit.target.strings)
                else:
                    orig = unit.source
                    trans = unit.target
                doc["source"] = orig
                doc["target"] = trans
                doc["notes"] = unit.getnotes()
                doc["locations"] = unit.getlocations()
                addlist.append(doc)
            if addlist:
                indexer.begin_transaction()
                try:
                    for add_item in addlist:
                        indexer.index_document(add_item)
                finally:
                    indexer.commit_transaction()
                    indexer.flush(optimize=optimize)
        except (base.ParseError, IOError, OSError):
            indexer.delete_doc({"pofilename": store.pootle_path})
            logging.error("Not indexing %s, since it is corrupt", store.pootle_path)

    def matchessearch(self, pofilename, search):
        """returns whether any items in the pofilename match the search (based on collected stats etc)"""
        # wrong file location in a "dirfilter" search?
        if search.dirfilter is not None and not pofilename.startswith(search.dirfilter):
            return False
        # search.assignedto == [None] means assigned to nobody
        if search.assignedto or search.assignedaction:
            if search.assignedto == [None]:
                assigns = self.non_db_state.pofiles[pofilename].getassigns().getunassigned(search.assignedaction)
            else:
                assigns = self.non_db_state.pofiles[pofilename].getassigns().getassigns()
                if search.assignedto is not None:
                    if search.assignedto not in assigns:
                        return False
                    assigns = assigns[search.assignedto]
                else:
                    assigns = reduce(lambda x, y: x+y, [userassigns.keys() for userassigns in assigns.values()], [])
                if search.assignedaction is not None:
                    if search.assignedaction not in assigns:
                        return False
        if search.matchnames:
            postats = self.getpostats(pofilename)
            for name in search.matchnames:
                if postats.get(name):
                    return True
            return False
        return True

    def indexsearch(self, search, returnfields):
        """returns the results from searching the index with the given search"""
        def do_search(indexer):
            searchparts = []
            if search.searchtext:
                # Split the search expression into single words. Otherwise xapian and
                # lucene would interprete the whole string as an "OR" combination of
                # words instead of the desired "AND".
                for word in search.searchtext.split():
                    # Generate a list for the query based on the selected fields
                    querylist = [(f, word) for f in search.searchfields]
                    textquery = indexer.make_query(querylist, False)
                    searchparts.append(textquery)
            if search.dirfilter:
                pofilenames = self.browsefiles(dirfilter=search.dirfilter)
                filequery = indexer.make_query([("pofilename", pofilename) for pofilename in pofilenames], False)
                searchparts.append(filequery)
            # TODO: add other search items
            limitedquery = indexer.make_query(searchparts, True)
            return indexer.search(limitedquery, returnfields)

        indexer = self.indexer
        if indexer != None:
            return do_search(indexer)
        else:
            return False

    def searchpofilenames(self, lastpofilename, search, includelast=False):
        """find the next pofilename that has items matching the given search"""
        if lastpofilename and not lastpofilename in self.non_db_state.pofiles:
            # accessing will autoload this file...
            self.non_db_state.pofiles[lastpofilename]
        searchpofilenames = None
        if self.has_index and search.searchtext:
            try:
                # TODO: move this up a level, use index to manage whole search, so we don't do this twice
                hits = self.indexsearch(search, "pofilename")
                # there will be only result for the field "pofilename" - so we just
                # pick the first
                searchpofilenames = dict.fromkeys([hit["pofilename"][0] for hit in hits])
            except:
                logging.error("Could not perform indexed search on %s. Index is corrupt.", lastpofilename)
                self._indexing_enabled = False
        for pofilename in self.iterpofilenames(lastpofilename, includelast):
            if searchpofilenames is not None:
                if pofilename not in searchpofilenames:
                    continue
            if self.matchessearch(pofilename, search):
                yield pofilename

    def searchpoitems(self, pofilename, lastitem, search):
        """finds the next item matching the given search"""

        def indexed(pofilename, search, lastitem):
            filesearch = search.copy()
            filesearch.dirfilter = pofilename
            hits = self.indexsearch(filesearch, "itemno")
            # there will be only result for the field "itemno" - so we just
            # pick the first
            all_items = (int(doc["itemno"][0]) for doc in hits)
            next_items = (search_item for search_item in all_items if search_item > lastitem)
            try:
                # Since we will call self.searchpoitems (the method in which we are)
                # every time a user clicks the next button, the loop which calls yield
                # on indexed will only need a single value from this generator. So we
                # only return a list with a single item.
                return [min(next_items)]
            except ValueError:
                return []

        def non_indexed(pofilename, search, lastitem):
            # Ask pofile for all the possible items which follow lastitem, based on
            # the criteria in search.
            pofile = self.getpofile(pofilename)
            items = pofile.iteritems(search, lastitem)
            if search.searchtext:
                # We'll get here if the user is searching for a piece of text and if no indexer
                # (such as Xapian or Lucene) is usable. First build a grepper...
                grepfilter = pogrep.GrepFilter(search.searchtext, search.searchfields, ignorecase=True)
                # ...then filter the items using the grepper.
                return (item for item in items if grepfilter.filterunit(pofile.getitem(item)))
            else:
                return items

        def get_items(pofilename, search, lastitem):
            if self.has_index and search.searchtext:
                try:
                    # Return an iterator using the indexer if indexing is available and if there is searchtext.
                    return indexed(pofilename, search, lastitem)
                except:
                    logging.error("Could not perform indexed search on %s. Index is corrupt.", pofilename)
                    self._indexing_enabled = False
            return non_indexed(pofilename, search, lastitem)

        for pofilename in self.searchpofilenames(pofilename, search, includelast=True):
            for item in get_items(pofilename, search, lastitem):
                yield pofilename, item
            # this must be set to None so that the next call to
            # get_items(self.getpofile(pofilename), search, lastitem) [see just above]
            # will start afresh with the first item in the next pofilename.
            lastitem = None

    ##############################################################################################

    def reassignpoitems(self, request, search, assignto, action):
        """reassign all the items matching the search to the assignto user(s) evenly, with the given action"""
        # remove all assignments for the given action
        self.unassignpoitems(request, search, None, action)
        assigncount = self.assignpoitems(request, search, assignto, action)
        return assigncount

    def assignpoitems(self, request, search, assignto, action):
        """assign all the items matching the search to the assignto user(s) evenly, with the given action"""
        if not check_permission("assign", request):
            raise PermissionError(_("You do not have rights to alter assignments here"))
        if search.searchtext:
            grepfilter = pogrep.GrepFilter(search.searchtext, None, ignorecase=True)
        if not isinstance(assignto, list):
            assignto = [assignto]
        usercount = len(assignto)
        assigncount = 0
        if not usercount:
            return assigncount
        pofilenames = [pofilename for pofilename in self.searchpofilenames(None, search, includelast=True)]
        wordcounts = [(pofilename, self.getpofile(pofilename).statistics.getquickstats()['totalsourcewords']) for pofilename in pofilenames]
        totalwordcount = sum([wordcount for pofilename, wordcount in wordcounts])

        wordsperuser = totalwordcount / usercount
        logging.debug("assigning %d words to %d user(s) %d words per user", totalwordcount, usercount, wordsperuser)
        usernum = 0
        userwords = 0
        for pofilename, wordcount in wordcounts:
            pofile = self.getpofile(pofilename)
            sourcewordcount = pofile.statistics.getunitstats()['sourcewordcount']
            for item in pofile.iteritems(search, None):
                # TODO: move this to iteritems
                if search.searchtext:
                    validitem = False
                    unit = pofile.getitem(item)
                    if grepfilter.filterunit(unit):
                        validitem = True
                    if not validitem:
                        continue
                itemwordcount = sourcewordcount[item]
                #itemwordcount = statsdb.wordcount(str(pofile.getitem(item).source))
                if userwords + itemwordcount > wordsperuser:
                    usernum = min(usernum+1, len(assignto)-1)
                    userwords = 0
                userwords += itemwordcount
                pofile.getassigns().assignto(item, assignto[usernum], action)
                assigncount += 1
        return assigncount

    def unassignpoitems(self, request, search, assignedto, action=None):
        """unassigns all the items matching the search to the assignedto user"""
        if not check_permission("assign", request):
            raise PermissionError(_("You do not have rights to alter assignments here"))
        if search.searchtext:
            grepfilter = pogrep.GrepFilter(search.searchtext, None, ignorecase=True)
        assigncount = 0
        for pofilename in self.searchpofilenames(None, search, includelast=True):
            pofile = self.getpofile(pofilename)
            for item in pofile.iteritems(search, None):
                # TODO: move this to iteritems
                if search.searchtext:
                    unit = pofile.getitem(item)
                    if grepfilter.filterunit(unit):
                        pofile.getassigns().unassign(item, assignedto, action)
                        assigncount += 1
                else:
                    pofile.getassigns().unassign(item, assignedto, action)
                    assigncount += 1
        return assigncount

    ##############################################################################################

    def combinestats(self, pofilenames=None):
        """combines translation statistics for the given po files (or all if None given)"""
        if pofilenames is None:
            pofilenames = self.non_db_state.pofilenames
        pofilenames = [pofilename for pofilename in pofilenames
                                     if pofilename != None and not os.path.isdir(pofilename)]
        total_stats = self.combine_totals(pofilenames)
        total_stats['units'] = self.combine_unit_stats(pofilenames)
        total_stats['assign'] = self.combineassignstats(pofilenames)
        return total_stats

    def combine_totals(self, pofilenames):
        totalstats = {}
        for pofilename in pofilenames:
            pototals = self.getpototals(pofilename)
            for name, items in pototals.iteritems():
                totalstats[name] = totalstats.get(name, 0) + pototals[name]
        return totalstats

    def combine_unit_stats(self, pofilenames):
        unit_stats = {}
        for pofilename in pofilenames:
            postats = self.getpostats(pofilename)
            for name, items in postats.iteritems():
                unit_stats.setdefault(name, []).extend([(pofilename, item) for item in items])
        return unit_stats

    def combineassignstats(self, pofilenames=None, action=None):
        """combines assign statistics for the given po files (or all if None given)"""
        assign_stats = {}
        for pofilename in pofilenames:
            assignstats = self.getassignstats(pofilename, action)
            for name, items in assignstats.iteritems():
                assign_stats.setdefault(name, []).extend([(pofilename, item) for item in items])
        return assign_stats

    def countwords(self, stats):
        """counts the number of words in the items represented by the stats list"""
        wordcount = 0
        for pofilename, item in stats:
            pofile = self.non_db_state.pofiles[pofilename]
            if 0 <= item < len(pofile.statistics.getunitstats()['sourcewordcount']):
                wordcount += pofile.statistics.getunitstats()['sourcewordcount'][item]
        return wordcount

    def track(self, pofilename, item, message):
        """sends a track message to the pofile"""
        self.non_db_state.pofiles[pofilename].track(item, message)

    def gettracks(self, pofilenames=None):
        """calculates translation statistics for the given po files (or all if None given)"""
        alltracks = []
        if pofilenames is None:
            pofilenames = self.non_db_state.pofilenames
        for pofilename in pofilenames:
            if not pofilename or os.path.isdir(pofilename):
                continue
            tracker = self.non_db_state.pofiles[pofilename].tracker
            items = tracker.keys()
            items.sort()
            for item in items:
                alltracks.append("%s item %d: %s" % (pofilename, item, tracker[item]))
        return alltracks

    def getpostats(self, pofilename):
        """calculates translation statistics for the given po file"""
        return self.non_db_state.pofiles[pofilename].statistics.getstats()

    def getpototals(self, pofilename):
        """calculates translation statistics for the given po file"""
        return self.non_db_state.pofiles[pofilename].statistics.getquickstats()

    def getassignstats(self, pofilename, action=None):
        """calculates translation statistics for the given po file (can filter by action if given)"""
        polen = self.getpototals(pofilename).get("total", 0)
        # Temporary code to avoid traceback. Was:
#        polen = len(self.getpostats(pofilename)["total"])
        assigns = self.non_db_state.pofiles[pofilename].getassigns().getassigns()
        assignstats = {}
        for username, userassigns in assigns.iteritems():
            allitems = []
            for assignaction, items in userassigns.iteritems():
                if action is None or assignaction == action:
                    allitems += [item for item in items if 0 <= item < polen and item not in allitems]
            if allitems:
                assignstats[username] = allitems
        return assignstats

    def getpofile(self, pofilename, freshen=True):
        """parses the file into a pofile object and stores in self.pofiles"""
        pofile = self.non_db_state.pofiles[pofilename]
        if freshen:
            pofile.pofreshen()
        return pofile

    def getpofilelen(self, pofilename):
        """returns number of items in the given pofilename"""
        pofile = self.getpofile(pofilename)
        return len(pofile.total)

    def getitems(self, pofilename, itemstart, itemstop):
        """returns a set of items from the pofile, converted to original and translation strings"""
        pofile = self.getpofile(pofilename)
        units = [pofile.units[index] for index in pofile.total[max(itemstart,0):itemstop]]
        return units

    ##############################################################################################

    is_terminology_project = property(lambda self: self.project.code == "terminology")
    is_template_project = property(lambda self: self.language.code == 'templates')

    stores = property(lambda self: Store.objects.filter(pootle_path__startswith=self.directory.pootle_path))

    def gettmsuggestions(self, pofile, item):
        """find all the TM suggestions for the given (pofile or pofilename) and item"""
        if isinstance(pofile, (str, unicode)):
            pofilename = pofile
            pofile = self.getpofile(pofilename)
        tmsuggestpos = pofile.gettmsuggestions(item)
        return tmsuggestpos

    def gettermbase(self, make_matcher):
        """returns this project's terminology store"""
        if self.is_terminology_project:
            query = self.stores
            if query.count() > 0:
                return make_matcher(self)
        else:
            termfilename = "pootle-terminology." + self.project.localfiletype
            try:
                store = Store.objects.get(pootle_path=termfilename)
                return make_matcher(store)
            except Store.DoesNotExist:
                pass
        raise StopIteration()

    def gettermmatcher(self):
        """returns the terminology matcher"""
        def make_matcher(termbase):
            newmtime = termbase.pomtime
            if newmtime != self.non_db_state.termmatchermtime:
                if self.is_terminology_project:
                    return match.terminologymatcher([store.file.store for store in self.stores.all()]), newmtime
                else:
                    return match.terminologymatcher(termbase), newmtime

        if self.non_db_state.termmatcher is None:
            try:
                self.non_db_state.termmatcher, self.non_db_state.termmatchermtime = self.gettermbase(make_matcher)
            except StopIteration:
                if not self.is_terminology_project:
                    try:
                        termproject = TranslationProject.objects.get(language=self.language_id, project__code='terminology')
                        self.non_db_state.termmatcher = termproject.gettermmatcher()
                        self.non_db_state.termmatchermtime = termproject.non_db_state.termmatchermtime
                    except TranslationProject.DoesNotExist:
                        pass
        return self.non_db_state.termmatcher

    ##############################################################################################

    def convert(self, pofilename, destformat):
        """converts the pofile to the given format, returning
        (etag_if_filepath, filepath_or_contents)"""
        pofile = self.getpofile(pofilename, freshen=False)
        destfilename = pofile.filename[:-len(self.fileext)] + destformat
        destmtime = statistics.getmodtime(destfilename)
        pomtime = statistics.getmodtime(pofile.filename)
        if pomtime and destmtime == pomtime:
            try:
                return pomtime, destfilename
            except Exception, e:
                logging.error("error reading cached converted file %s: %s", destfilename, e)
        pofile.pofreshen()
        converters = {"csv": po2csv.po2csv,
                      "xlf": po2xliff.po2xliff,
                      "po": xliff2po.xliff2po,
                      "ts": po2ts.po2ts,
                      "mo": pocompile.POCompile}
        converterclass = converters.get(destformat, None)
        if converterclass is None:
            raise ValueError("No converter available for %s" % destfilename)
        contents = converterclass().convertstore(pofile)
        if not isinstance(contents, basestring):
            contents = str(contents)
        try:
            destfile = open(destfilename, "w")
            destfile.write(contents)
            destfile.close()
            currenttime, modtime = time.time(), pofile.pomtime
            os.utime(destfilename, (currenttime, modtime))
            return modtime, destfilename
        except Exception, e:
            logging.error("error caching converted file %s: %s", destfilename, e)
        return False, contents

    ##############################################################################################


    def _find_matching_unit(self, singular, plural=None, n=1):
        for store in self.stores:
            store.file.store.require_index()
            unit = store.file.store.findunit(singular)
            if unit is not None and unit.istranslated():
                if unit.hasplural() and n != 1:
                    nplural, pluralequation = store.file.store.getheaderplural()
                    if pluralequation:
                        pluralfn = gettext.c2py(pluralequation)
                        target =  unit.target.strings[pluralfn(n)]
                        if target is not None:
                            return target
                else:
                    return unit.target

        # no translation found
        if n != 1 and plural is not None:
            return plural
        else:
            return singular


    def gettext(self, message):
        """uses the project as a live translator for the given message"""
        return str(self._find_matching_unit(message))

    def ugettext(self, message):
        """gets the translation of the message by searching through
        all the pofiles (unicode version)"""
        return unicode(self._find_matching_unit(message))

    def ngettext(self, singular, plural, n):
        """gets the plural translation of the message by searching
        through all the pofiles"""
        return str(self._find_matching_unit(singular, plural, n))

    def ungettext(self, singular, plural, n):
        """gets the plural translation of the message by searching
        through all the pofiles (unicode version)"""
        return unicode(self._find_matching_unit(singular, plural, n))

def set_data(sender, instance, **kwargs):
    project_dir = instance.project.get_real_path()
    ext         = project_tree.get_extension(instance.language, instance.project)
    instance.abs_real_path = project_tree.get_translation_project_dir(instance.language, project_dir, instance.file_style)
    instance.directory = Directory.objects.root\
        .get_or_make_subdir(instance.language.code)\
        .get_or_make_subdir(instance.project.code)

pre_save.connect(set_data, sender=TranslationProject)

def delete_directory(sender, instance, **kwargs):
    instance.directory.delete()

#pre_delete.connect(delete_directory, sender=TranslationProject)

def add_pomtime(sender, instance, **kwargs):
    instance.pomtime = 0

post_init.connect(add_pomtime, sender=TranslationProject)

def scan_languages(sender, instance, **kwargs):
    for language in Language.objects.all():
        create_translation_project(language, instance)

post_save.connect(scan_languages, sender=Project)

def scan_projects(sender, instance, **kwargs):
    for project in Project.objects.all():
        create_translation_project(instance, project)

post_save.connect(scan_projects, sender=Language)
