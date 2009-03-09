#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2009 Zuza Software Foundation
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

import time
import os
import cStringIO
import traceback
import gettext
import subprocess
import datetime
import zipfile

from django.contrib.auth.models         import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.conf                        import settings
from django.db                          import models
from django.db.models.signals           import pre_delete, post_init

from translate.filters import checks
from translate.convert import po2csv, po2xliff, xliff2po, po2ts, po2oo
from translate.tools   import pocompile, pogrep
from translate.search  import match, indexing
from translate.storage import factory, statsdb, base, versioncontrol

from pootle_app.profile   import *
from pootle_app.core      import Project, Language
from pootle_app.fs_models import Directory, Store
from pootle_app           import project_tree, store_iteration

from Pootle            import pan_app, pootlefile, statistics
from Pootle.scripts    import hooks
from Pootle.pootlefile import relative_real_path, absolute_real_path

class TranslationProjectNonDBState(object):
    def __init__(self, parent):
        self.parent = parent
        # terminology matcher
        self.termmatcher = None
        self.termmatchermtime = None        
        self._indexing_enabled = True
        self._index_initialized = False

translation_project_non_db_state = {}

def make_translation_project(language, project):
    project_dir = project_tree.get_project_dir(project)
    ext         = project_tree.get_extension(language, project)
    file_style  = project_tree.get_file_style(project_dir, language, project, ext=ext)
    real_path   = project_tree.get_translation_project_dir(language, project_dir, file_style)
    directory   = Directory.objects.root\
        .get_or_make_subdir(language.code)\
        .get_or_make_subdir(project.code)
    translation_project = TranslationProject(project       = project,
                                             language      = language,
                                             directory     = directory,
                                             abs_real_path = real_path,
                                             file_style    = file_style)
    translation_project.save()
    return translation_project
    
def scan_translation_projects():
    def get_or_make(language, project):
        try:
            return TranslationProject.objects.get(language=language, project=project)
        except TranslationProject.DoesNotExist:
            try:
                return make_translation_project(language, project)
            except OSError:
                return None
            except IndexError:
                return None

    for language in Language.objects.include_hidden().all():
        for project in Project.objects.all():
            translation_project = get_or_make(language, project)
            if translation_project is not None:
                project_tree.scan_translation_project_files(translation_project)

class TranslationProject(models.Model):
    index_directory  = ".translation_index"

    class Meta:
        unique_together = ('language', 'project')

    language   = models.ForeignKey(Language, db_index=True)
    project    = models.ForeignKey(Project,  db_index=True)
    real_path  = models.FilePathField()
    directory  = models.ForeignKey('Directory')
    file_style = models.CharField(max_length=255, blank=True, null=False, default="")

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

    def _get_abs_real_path(self):
        return absolute_real_path(self.real_path)

    def _set_abs_real_path(self, value):
        self.real_path = relative_real_path(value)

    abs_real_path = property(_get_abs_real_path, _set_abs_real_path)

    def _get_checker(self):
        checkerclasses = [checks.projectcheckers.get(self.project.checkstyle,
                                                     checks.StandardChecker), 
                          checks.StandardUnitChecker]
        return checks.TeeChecker(checkerclasses=checkerclasses, 
                                 errorhandler=self.filtererrorhandler,
                                 languagecode=self.language.code)

    checker = property(_get_checker)

    def filtererrorhandler(self, functionname, str1, str2, e):
        print "error in filter %s: %r, %r, %s" % (functionname, str1, str2, e)
        return False

    def _get_non_db_state(self):
        if self.id not in translation_project_non_db_state:
            translation_project_non_db_state[self.id] = TranslationProjectNonDBState(self)
        return translation_project_non_db_state[self.id]

    non_db_state = property(_get_non_db_state)

    def get_quick_stats(self):
        return self.directory.get_quick_stats(self.checker)

    def _get_indexer(self):
        if self.non_db_state._indexing_enabled:
            try:
                indexer = self.make_indexer()
                if not self.non_db_state._index_initialized:
                    self.init_index(indexer)
                    self.non_db_state._index_initialized = True
                return indexer
            except Exception, e:
                import traceback
                traceback.print_exc()
                print "Could not intialize indexer for %s in %s: %s" % (self.project.code, self.language.code, str(e))
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

    def getuploadpath(self, dirname, localfilename):
        """gets the path of a translation file being uploaded securely, creating directories as neccessary"""
        if os.path.isabs(dirname) or dirname.startswith("."):
            raise ValueError("invalid/insecure file path: %s" % dirname)
        if os.path.basename(localfilename) != localfilename or localfilename.startswith("."):
            raise ValueError("invalid/insecure file name: %s" % localfilename)
        if self.filestyle == "gnu":
            if not pan_app.get_po_tree().languagematch(self.languagecode, localfilename[:-len("."+self.fileext)]):
                raise ValueError("invalid GNU-style file name %s: must match '%s.%s' or '%s[_-][A-Z]{2,3}.%s'" % (localfilename, self.languagecode, self.fileext, self.languagecode, self.fileext))
        dircheck = self.abs_real_path
        for part in dirname.split(os.sep):
            dircheck = os.path.join(dircheck, part)
            if dircheck and not os.path.isdir(dircheck):
                os.mkdir(dircheck)
        return os.path.join(self.abs_real_path, dirname, localfilename)

    def uploadfile(self, request, dirname, filename, contents, overwrite=False):
        """uploads an individual file"""
        pathname = self.getuploadpath(dirname, filename)
        for extention in ["xliff", "xlf", "xlff"]:
            if filename.endswith(extention):
                pofilename = filename[:-len(os.extsep+extention)] + os.extsep + self.fileext
                popathname = self.getuploadpath(dirname, pofilename)
                break
        else:
            pofilename = filename
            popathname = pathname

        user_permissions = self.get_permissions(request.user)

        if os.path.exists(popathname) and not overwrite:
            origpofile = self.getpofile(os.path.join(dirname, pofilename))
            newfileclass = factory.getclass(pathname)
            infile = cStringIO.StringIO(contents)
            newfile = newfileclass.parsefile(infile)
            if "administrate" in user_permissions.name_map:
                origpofile.mergefile(newfile, request.user.username)
            elif "translate" in user_permissions.name_map:
                origpofile.mergefile(newfile, request.user.username, allownewstrings=False)
            elif "suggest" in user_permissions.name_map:
                origpofile.mergefile(newfile, request.user.username, suggestions=True)
            else:
                raise RightsError(_("You do not have rights to upload files here"))
        else:
            if overwrite and not ("administrate" in user_permissions.name_map or \
                                      "overwrite" in user_permissions.name_map):
                raise RightsError(_("You do not have rights to overwrite files here"))
            elif not os.path.exists(popathname) and not ("administrate" in user_permissions.name_map or \
                                                             "overwrite" in user_permissions.name_map):
                raise RightsError(_("You do not have rights to upload new files here"))
            outfile = open(popathname, "wb")
            outfile.write(contents)
            outfile.close()

    def updatepofile(self, request, dirname, pofilename):
        """updates an individual PO file from version control"""
        # read from version control
        pathname = self.getuploadpath(dirname, pofilename)
        try:
            pathname = hooks.hook(self.project.code, "preupdate", pathname)
        except:
            pass

        if os.path.exists(pathname):
            popath = os.path.join(dirname, pofilename)

            currentpofile = self.getpofile(popath)
            # matching current file with BASE version
            # TODO: add some locking here...
            # reading new version of file
            versioncontrol.updatefile(pathname)
            newpofile = pootlefile.pootlefile(self, popath)
            newpofile.pofreshen()
            newpofile.mergefile(currentpofile, "versionmerge")
            self.non_db_state.pofiles[pofilename] = newpofile
        else:
            versioncontrol.updatefile(pathname)

        get_profile(request.user).add_message("Updated file: <em>%s</em>" % pofilename)

        try:
            hooks.hook(self.project.code, "postupdate", pathname)
        except:
            pass

        if newpofile:
            # Update po index for new file
            self.stats = {}
            for xpofilename in self.non_db_state.pofilenames:
                self.getpostats(xpofilename)
                self.non_db_state.pofiles[xpofilename] = pootlefile.pootlefile(self, xpofilename)
                self.non_db_state.pofiles[xpofilename].statistics.getstats()
                self.updateindex(self.indexer, xpofilename)
            self.projectcache = {}

    def runprojectscript(self, scriptdir, target, extraargs = []):
        currdir = os.getcwd()
        script = os.path.join(scriptdir, self.project.code)
        try:
            os.chdir(scriptdir)
            cmd = [script, target]
            cmd.extend(extraargs)
            subprocess.call(cmd)
        except:
            pass # If something goes wrong, we just continue without worrying
        os.chdir(currdir)

    def commitpofile(self, request, dirname, pofilename):
        """commits an individual PO file to version control"""
        if "commit" not in self.getrights(request.user):
            raise RightsError(_("You do not have rights to commit files here"))
        pathname = self.getuploadpath(dirname, pofilename)
        stats = self.getquickstats([os.path.join(dirname, pofilename)])
        statsstring = "%d of %d messages translated (%d fuzzy)." % \
                (stats["translated"], stats["total"], stats["fuzzy"])

        message="Commit from %s by user %s, editing po file %s. %s" % (pan_app.prefs.title, request.user.username, pofilename, statsstring)
        author=request.user.username
        fulldir = os.path.split(pathname)[0]
     
        try:
            filestocommit = hooks.hook(self.project.code, "precommit", pathname, author=author, message=message)
        except ImportError:
            # Failed to import the hook - we're going to assume there just isn't a hook to
            # import.    That means we'll commit the original file.
            filestocommit = [pathname]

        success = True
        try:
            for file in filestocommit:
                versioncontrol.commitfile(file, message=message, author=author)
                get_profile(request.user).add_message("Committed file: <em>%s</em>" % file)
        except Exception, e:
            print "Failed to commit files: %s" % e
            get_profile(request.user).add_message("Failed to commit file: %s" % e)
            success = False 
        try:
            hooks.hook(self.project.code, "postcommit", pathname, success=success)
        except:
            pass

    def initialize(self):
        try:
            hooks.hook(self.project.code, "initialize", self.projectdir, self.language.code)
            self.non_db_state.scanpofiles()
        except Exception, e:
            print "Failed to initialize (%s): %s" % (languagecode, e)

    def filtererrorhandler(self, functionname, str1, str2, e):
        print "error in filter %s: %r, %r, %s" % (functionname, str1, str2, e)
        return False

    ##############################################################################################

    def getarchive(self, pofilenames):
        """returns an archive of the given filenames"""
        try:
            # using zip command line is fast
            from tempfile import mkstemp
            # The temporary file below is opened and immediately closed for security reasons
            fd, tempzipfile = mkstemp(prefix='pootle', suffix='.zip')
            os.close(fd)
            os.system("cd %s ; zip -r - %s > %s" % (self.abs_real_path, " ".join(pofilenames), tempzipfile))
            filedata = open(tempzipfile, "r").read()
            if filedata:
                return filedata
        finally:
            if os.path.exists(tempzipfile):
                os.remove(tempzipfile)

        # but if it doesn't work, we can do it from python
        archivecontents = cStringIO.StringIO()
        archive = zipfile.ZipFile(archivecontents, 'w', zipfile.ZIP_DEFLATED)
        for pofilename in pofilenames:
            pofile = self.getpofile(pofilename)
            archive.write(pofile.filename, pofilename)
        archive.close()
        return archivecontents.getvalue()

    def uploadarchive(self, request, dirname, archivecontents, overwrite=False):
        """uploads the files inside the archive"""

        def unzip_external(archivecontents):
            from tempfile import mkdtemp, mkstemp
            tempdir = mkdtemp(prefix='pootle')
            tempzipfd, tempzipname = mkstemp(prefix='pootle', suffix='.zip')

            try:
                os.write(tempzipfd, archivecontents)
                os.close(tempzipfd)

                import subprocess
                if subprocess.call(["unzip", tempzipname, "-d", tempdir]):
                    raise zipfile.BadZipfile(_("Error while extracting archive"))

                def upload(basedir, path, files):
                    for fname in files:
                        if not os.path.isfile(os.path.join(path, fname)):
                            continue
                        if not fname.endswith(os.extsep + self.fileext):
                            print "error adding %s: not a %s file" % (fname, os.extsep + self.fileext)
                            continue
                        fcontents = open(os.path.join(path, fname), 'rb').read()
                        self.uploadfile(request, path[len(basedir)+1:], fname, fcontents, overwrite)
                os.path.walk(tempdir, upload, tempdir)
                return
            finally:
                # Clean up temporary file and directory used in try-block
                import shutil
                os.unlink(tempzipname)
                shutil.rmtree(tempdir)

        def unzip_python(archivecontents):
            archive = zipfile.ZipFile(cStringIO.StringIO(archivecontents), 'r')
            # TODO: find a better way to return errors...
            for filename in archive.namelist():
                if not filename.endswith(os.extsep + self.fileext):
                    print "error adding %s: not a %s file" % (filename, os.extsep + self.fileext)
                    continue
                contents = archive.read(filename)
                subdirname, pofilename = os.path.dirname(filename), os.path.basename(filename)
                try:
                    # TODO: use zipfile info to set the time and date of the file
                    self.uploadfile(request, os.path.join(dirname, subdirname), pofilename, contents, overwrite)
                except ValueError, e:
                    print "error adding %s" % filename, e
                    continue
            archive.close()

        # First we try to use "unzip" from the system, otherwise fall back to using
        # the slower zipfile module (below)...
        try:
            unzip_external(archivecontents)
        except Exception:
            unzip_python(archivecontents)

    def ootemplate(self):
        """Tests whether this project has an OpenOffice.org template SDF file in
        the templates directory."""
        projectdir = os.path.join(pan_app.get_po_tree().podirectory, self.project.code)
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
        inputdir = os.path.join(pan_app.get_po_tree().podirectory, self.project.code, self.languagecode)
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
        def do_update(pootle_file):
            self.update_index(indexer, pootle_file, optimize=False)

        for store in Store.objects.filter(pootle_path__startswith=self.directory.pootle_path):
            pootlefile.with_store(self, store, do_update)

    def update_index(self, indexer, pofile, items=None, optimize=True):
        """updates the index with the contents of pofilename (limit to items if given)

        There are three reasons for calling this function:
            1. creating a new instance of L{TranslationProject} (see L{initindex})
                    -> check if the index is up-to-date / rebuild the index if necessary
            2. translating a unit via the web interface
                    -> (re)index only the specified unit(s)

        The argument L{items} should be None for 1.

        known problems:
            1. This function should get called, when the po file changes externally.
                 The function "pofreshen" in pootlefile.py would be the natural place
                 for this. But this causes circular calls between the current (r7514)
                 statistics code and "updateindex" leading to indexing database lock
                 issues.

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
            pomtime = statistics.getmodtime(pofile.filename)
            pofilenamequery = indexer.make_query([("pofilename", pofile.store.pootle_path)], True)
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
                print "updating", self.language.code, "index for", pofile.store.pootle_path, "items", items
                # delete the relevant items from the database
                itemsquery = indexer.make_query([("itemno", str(itemno)) for itemno in items], False)
                indexer.delete_doc([pofilenamequery, itemsquery])
            else:
                # (items is None)
                # The po file is not indexed - or it was changed externally (see
                # "pofreshen" in pootlefile.py).
                print "updating", self.project.code, self.language.code, "index for", pofile.store.pootle_path
                # delete all items of this file
                indexer.delete_doc({"pofilename": pofile.store.pootle_path})
            pofile.pofreshen()
            if items is None:
                # rebuild the whole index
                items = range(pofile.statistics.getitemslen())
            addlist = []
            for itemno in items:
                unit = pofile.getitem(itemno)
                doc = {"pofilename": pofile.store.pootle_path, "pomtime": str(pomtime), "itemno": str(itemno)}
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
            indexer.delete_doc({"pofilename": pofile.store.pootle_path})
            print "Not indexing %s, since it is corrupt" % (pofile.store.pootle_path,)

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
                print "Could not perform indexed search on %s. Index is corrupt." % lastpofilename
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
                    print "Could not perform indexed search on %s. Index is corrupt." % pofilename
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
        if not "assign" in self.getrights(request.user):
            raise RightsError(_("You do not have rights to alter assignments here"))
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
        print "assigning", totalwordcount, "words to", usercount, "user(s)", wordsperuser, "words per user"
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
        if not "assign" in self.getrights(request.user):
            raise RightsError(_("You do not have rights to alter assignments here"))
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

    def getquickstats(self, pofilenames=None):
        """Gets translated and total stats and wordcounts without doing calculations returning dictionary."""
        if pofilenames is None:
            pofilenames = self.non_db_state.pofilenames
        result =    {"translatedsourcewords": 0, "translated": 0,
                             "fuzzysourcewords": 0, "fuzzy": 0,
                             "totalsourcewords": 0, "total": 0}
        for stats in (self.non_db_state.pofiles[key].statistics.getquickstats() for key in pofilenames):
            for key in result:
                result[key] += stats[key]
        return result

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

    def getsuggestions(self, pofile, item):
        """find all the suggestions submitted for the given (pofile or pofilename) and item"""
        if isinstance(pofile, (str, unicode)):
            pofilename = pofile
            pofile = self.getpofile(pofilename)
        suggestpos = pofile.getsuggestions(item)
        return suggestpos

    ##############################################################################################

    is_terminology_project = property(lambda self: self.project.code == "terminology")

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
                for store in query.all():
                    # We just want to touch the stores, since this
                    # will automatically pull them into the cache and
                    # freshen them.
                    pootlefile.with_store(self, store, lambda _x: None)
                return make_matcher(self)
        else:
            termfilename = "pootle-terminology." + self.project.localfiletype
            try:
                store = Store.objects.get(pootle_path=termfilename)
                return pootlefile.with_store(pootle_file.translation_project, store, make_matcher)
            except Store.DoesNotExist:
                pass
        raise StopIteration()

    def gettermmatcher(self):
        """returns the terminology matcher"""
        def make_matcher(termbase):
            newmtime = termbase.pomtime
            if newmtime != self.non_db_state.termmatchermtime:
                if self.is_terminology_project:
                    def init(pootle_files):
                        return match.terminologymatcher(pootle_files), newmtime
                    return pootlefile.with_stores(self, self.stores.all(), init)
                else:
                    def init(pootle_file):
                        return match.terminologymatcher(termbase), newmtime
                    return pootlefile.with_store(self, termbase, init)

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
                print "error reading cached converted file %s: %s" % (destfilename, e)
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
            print "error caching converted file %s: %s" % (destfilename, e)
        return False, contents

    ##############################################################################################

    def _find_message(self, singular, plural, n, get_translation):
        for store in Store.objects.filter(pootle_path__startswith=self.directory.pootle_path):
            translation = pootlefile.with_pootle_file(self, store.abs_real_path, get_translation)
            if translation is not None:
                return translation
        if n == 1:
            return singular
        else:
            return plural

    def gettext(self, message):
        """uses the project as a live translator for the given message"""
        def get_translation(pofile):
            try:
                if pofile.pofreshen() or not hasattr(pofile, "sourceindex"):
                    pofile.makeindex()
                unit = pofile.sourceindex.get(message, None)
                if unit is not None and unit.istranslated():
                    tmsg = unit.target
                    if tmsg is not None:
                        return tmsg
            except Exception, e:
                print "error reading translation from pofile %s: %s" % (pofilename, e)
                raise
        return self._find_message(message, None, 1, get_translation)

    def ugettext(self, message):
        """gets the translation of the message by searching through all the pofiles (unicode version)"""
        def get_translation(pofile):
            try:
                if pofile.pofreshen() or not hasattr(pofile, "sourceindex"):
                    pofile.makeindex()
                unit = pofile.sourceindex.get(message, None)
                if unit is not None and unit.istranslated():
                    tmsg = unit.target
                    if tmsg is not None:
                        if isinstance(tmsg, unicode):
                            return tmsg
                        else:
                            return unicode(tmsg, pofile.encoding)
            except Exception, e:
                print "error reading translation from pofile %s: %s" % (pofilename, e)
                raise
        return unicode(self._find_message(message, None, 1, get_translation))

    def ungettext(self, singular, plural, n):
        """gets the plural translation of the message by searching through all the pofiles (unicode version)"""
        def get_translation(pofile):
            try:
                if pofile.pofreshen() or not hasattr(pofile, "sourceindex"):
                    pofile.makeindex()
                nplural, pluralequation = pofile.getheaderplural()
                if pluralequation:
                    pluralfn = gettext.c2py(pluralequation)
                    unit = pofile.sourceindex.get(singular, None)
                    if unit is not None and unit.istranslated():
                        tmsg = unit.target.strings[pluralfn(n)]
                        if tmsg is not None:
                            if isinstance(tmsg, unicode):
                                return tmsg
                            else:
                                return unicode(tmsg, pofile.encoding)
            except Exception, e:
                print "error reading translation from pofile %s: %s" % (pofilename, e)
                raise
        return unicode(self._find_message(singular, plural, n, get_translation))

# def create_default_rights(sender, instance, **kwargs):
#     def make_right(user, permissions):
#         profile = get_profile(user)
#         permission_set = PermissionSet(profile=profile, translation_project=instance)
#         permission_set.save()
#         permission_set.permissions = permissions
#         permission_set.save()

#     # Get right objects corresponding to each of the 'special' users -
#     # i.e. users such as 'nobody' and 'default'
#     special_rights = PermissionSet.objects.select_related('profile__user__username')\
#         .filter(profile__user__username__in=User.objects.special_usernames, translation_project=instance)

#     # Get the usernames associated with these rights
#     special_rights_usernames = [right.profile.user.username for right in special_rights]
#     view_permission = get_pootle_permission('view')
#     # Get the special users which don't have rights objects
#     missing_permission_users = [user for user in User.objects.get_special_users() if not user.username in special_rights_usernames]
#     # For each of these users, create a Right object
#     for user in missing_permission_users:
#         make_right(user, [view_permission])

# def create_null_goal(sender, instance, **kwargs):
#     if Goal.objects.filter(translation_project=instance).count() == 0:
#         goal = Goal(name='', translation_project=instance)
#         goal.save()

def delete_directory(sender, instance, **kwargs):
    instance.directory.delete()

#pre_delete.connect(delete_directory, sender=TranslationProject)

def add_pomtime(sender, instance, **kwargs):
    instance.pomtime = 0

post_init.connect(add_pomtime, sender=TranslationProject)
