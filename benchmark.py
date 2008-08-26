#!/usr/bin/env python
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

from Pootle import pootlefile
from Pootle import projects
from Pootle import potree
from Pootle import pootle
from Pootle import users
from translate.storage import po
from translate.search import indexing
import os
import profile
import pstats

class PootleBenchmarker:
    """class to aid in benchmarking pootle"""
    StoreClass = pootlefile.pootlefile
    UnitClass = pootlefile.pootleunit
    def __init__(self, test_dir):
        """sets up benchmarking on the test directory"""
        self.test_dir = os.path.abspath(test_dir)
        self.project_dir = os.path.join(self.test_dir, "benchmark")
        self.po_dir = os.path.join(self.project_dir, "zxx")

    def clear_test_dir(self):
        """removes the given directory"""
        if os.path.exists(self.test_dir):
            for dirpath, subdirs, filenames in os.walk(self.test_dir, topdown=False):
                for name in filenames:
                    os.remove(os.path.join(dirpath, name))
                for name in subdirs:
                    os.rmdir(os.path.join(dirpath, name))
        if os.path.exists(self.test_dir): os.rmdir(self.test_dir)
        assert not os.path.exists(self.test_dir)

    def setup_server(self):
        """gets a pootle server"""
        cwd = os.path.abspath(os.path.curdir)
        parser = pootle.PootleOptionParser()
        prefsfile = os.path.join(self.test_dir, "pootle.prefs")
        pootleprefsstr = """
importmodules.pootleserver = 'Pootle.pootle'
Pootle:
  serverclass = pootleserver.PootleServer
  sessionkey = 'dummy'
  baseurl = "/"
  userprefs = "users.prefs"
  podirectory = "%s"
  projects.benchmark:
    fullname = "Benchmark"
    description = "Benchmark auto-created files"
    checkstyle = "standard"
    localfiletype = "po"
  languages.zxx.fullname = "Test Language"
""" % (self.test_dir)
        open(prefsfile, "w").write(pootleprefsstr)
        userprefsfile = os.path.join(self.test_dir, "users.prefs")
        open(userprefsfile, "w").write("testuser.activated=1\ntestuser.passwdhash = 'dd82c1882969461de74b46427961ea2c'\n")
        options, args = parser.parse_args(["--prefsfile=%s" % prefsfile])
        options.servertype = "dummy"
        self.server = parser.getserver(options)
        os.chdir(cwd)
        return self.server

    def get_session(self):
        """gets a new session object"""
        return users.PootleSession(self.server.sessioncache, self.server)

    def create_sample_files(self, num_dirs, files_per_dir, strings_per_file, source_words_per_string, target_words_per_string):
        """creates sample files for benchmarking"""
        if not os.path.exists(self.test_dir):
            os.mkdir(self.test_dir)
        if not os.path.exists(self.project_dir):
            os.mkdir(self.project_dir)
        if not os.path.exists(self.po_dir):
            os.mkdir(self.po_dir)
        for dirnum in range(num_dirs):
            if num_dirs > 1:
                dirname = os.path.join(self.po_dir, "sample_%d" % dirnum)
                if not os.path.exists(dirname):
                    os.mkdir(dirname)
            else:
                dirname = self.po_dir
            for filenum in range(files_per_dir):
                sample_file = self.StoreClass(pofilename=os.path.join(dirname, "file_%d.po" % filenum))
                for stringnum in range(strings_per_file):
                    source_string = " ".join(["word%d" % i for i in range(source_words_per_string)])
                    sample_unit = sample_file.addsourceunit(source_string)
                    sample_unit.target = " ".join(["drow%d" % i for i in range(target_words_per_string)])
                sample_file.savepofile()

    def parse_po_files(self):
        """parses all the po files in the test directory into memory"""
        count = 0
        for dirpath, subdirs, filenames in os.walk(self.po_dir, topdown=False):
            for name in filenames:
                pofilename = os.path.join(dirpath, name)
                parsedfile = po.pofile(open(pofilename, 'r'))
                count += len(parsedfile.units)
        print "counted %d units" % count

    def parse_and_create_stats(self):
        """parses all the po files in the test directory into memory, using pootlefile, which creates Stats"""
        count = 0
        indexing.HAVE_INDEXER = False
        for dirpath, subdirs, filenames in os.walk(self.po_dir, topdown=False):
            for name in filenames:
                pofilename = os.path.join(dirpath, name)
                parsedfile = pootlefile.pootlefile(pofilename=pofilename)
                count += len(parsedfile.units)
        print "stats on %d units" % count

    def parse_and_create_index(self):
        """parses all the po files in the test directory into memory, using pootlefile, and allow index creation"""
        count = 0
        indexing.HAVE_INDEXER = True
        self.server.potree.projectcache.clear()
        project = self.server.potree.getproject("zxx", "benchmark")
        for name in project.browsefiles():
            count += len(project.getpofile(name).units)
        print "indexed %d units" % count
        assert os.path.exists(os.path.join(self.po_dir, ".poindex-%s-%s" % (project.projectcode, project.languagecode)))

    def generate_main_page(self):
        """tests generating the main page"""
        session = self.get_session()
        page = self.server.getpage(["index.html"], session, {})
        print page.templatevars

    def generate_projectindex_page(self):
        """tests generating the index page for the project"""
        session = self.get_session()
        assert self.server.potree.haslanguage("zxx")
        assert self.server.potree.hasproject("zxx", "benchmark")
        page = self.server.getpage(["zxx", "benchmark"], session, {})
        print page.templatevars

    def generate_translation_page(self):
        """tests generating the translation page for the file"""
        session = self.get_session()
        page = self.server.getpage(["zxx", "benchmark", "translate.html"], session, {})
        print page.templatevars

    def submit_translation_change(self):
        """tests generating the translation page for the file"""
        session = self.get_session()
        project = self.server.potree.getproject("zxx", "benchmark")
        project.setrights(None, ["view", "translate"])
        pofilename = project.browsefiles()[0]
        args = {"pofilename": pofilename, "submit0": "true", "trans0": "changed"}
        page = self.server.getpage(["zxx", "benchmark", "translate.html"], session, args)
        pofile = project.getpofile(pofilename)
        print str(pofile.getitem(0))
        # assert fails because of multistring
        # assert pofile.getitem(0).unquotedmsgstr == "changed"
        print page.templatevars

if __name__ == "__main__":
    for sample_file_sizes in [
      # num_dirs, files_per_dir, strings_per_file, source_words_per_string, target_words_per_string
      # (1, 1, 1, 1, 1),
      (1, 1, 30, 10, 10),
      # (1, 5, 10, 10, 10),
      (1, 10, 10, 10, 10),
      (5, 10, 10, 10, 10),
      # (5, 10, 100, 20, 20),
      # (10, 20, 100, 10, 10),
      ]:
        benchmarker = PootleBenchmarker("BenchmarkDir")
        benchmarker.clear_test_dir()
        benchmarker.create_sample_files(*sample_file_sizes)
        benchmarker.setup_server()
        methods = ["parse_po_files", "parse_and_create_stats", "parse_and_create_index",
                   "generate_main_page", "generate_projectindex_page", "generate_translation_page",
                   "submit_translation_change",
                  ]
        for methodname in methods:
            print methodname, "%d dirs, %d files, %d strings, %d/%d words" % sample_file_sizes
            print "_______________________________________________________"
            statsfile = methodname + '_%d_%d_%d_%d_%d.stats' % sample_file_sizes
            profile.run('benchmarker.%s()' % methodname, statsfile)
            stats = pstats.Stats(statsfile)
            stats.sort_stats('cumulative').print_stats(20)
            print "_______________________________________________________"
        benchmarker.clear_test_dir()

