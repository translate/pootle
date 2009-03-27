#!/usr/bin/env python

"""Basic infrastructure for creating an environment for testing webservers
This gets used by test_cmdlineserver / test_service / test_apache (which are for different webservers)
The top-level tests are then in test_client / test_ie / test_mozilla etc
These can then be layered on top of different test servers"""

from Pootle import pootle
from jToolkit.web import simplewebserver
from jToolkit.web import session
from jToolkit.data import dates
from jToolkit import prefs
import os

sessioncache = session.SessionCache()

def isclassmethod(cls, method):
    """returns whether the given method (accessed as a class attribute) is a classmethod"""
    return method.im_self == cls

class TestCreate(object):
    """a test class to run tests on a test Pootle Server"""
    def setup_class(cls):
        """create the testing environment"""
        print "setup_class called on", cls.__name__
        cls.save_attribs = cls.__dict__.keys()
        cls.setup_testdir()
        # some testing methods find recreating the webserver per test easier
        if isclassmethod(cls, cls.setup_webserver):
            cls.webserver = cls.setup_webserver()
        else:
            cls.webserver = None
        setupprefs = cls.make_prefs()
        open(cls.prefsfile, "w").write(setupprefs.getsource())
        cls.prefs = prefs.PrefsParser(cls.prefsfile)
        cls.prefs.resolveimportmodules()

        cls.testuser = u"testuser"
        cls.testpass = u""

        if isclassmethod(cls, cls.setup_pootleserver):
            cls.setup_pootleserver()

    def setup_testdir(cls):
        """sets up a test directory"""
        cls.testdir = "%s_testdir" % (cls.__name__)
        cls.cleardir(cls.testdir)
        os.mkdir(cls.testdir)
        cls.podir = os.path.join(cls.testdir, "po")
        os.mkdir(cls.podir)
        cls.prefsfile = os.path.join(cls.testdir, "%s.prefs" % (cls.__name__))
    setup_testdir = classmethod(setup_testdir)

    def teardown_testdir(cls):
        """makes sure the test directory is clear"""
        cls.cleardir(cls.testdir)
    teardown_testdir = classmethod(teardown_testdir)

    def teardown_class(cls):
        """removes the attributes set up by setup_class"""
        if os.path.exists(cls.prefsfile):
            os.remove(cls.prefsfile)
        cls.teardown_testdir()
        cls.teardown_attribs()

    def cleardir(cls, dirname):
        """removes the given directory"""
        if os.path.exists(dirname):
            for dirpath, subdirs, filenames in os.walk(dirname, topdown=False):
                for name in filenames:
                    os.remove(os.path.join(dirpath, name))
                for name in subdirs:
                    os.rmdir(os.path.join(dirpath, name))
        if os.path.exists(dirname): os.rmdir(dirname)
        assert not os.path.exists(dirname)
    cleardir = classmethod(cleardir)

    def teardown_attribs(cls):
        """removes class attributes that have been set while running"""
        save_attribs = cls.save_attribs
        for attrib in cls.__dict__.keys():
            if attrib not in save_attribs:
                delattr(cls, attrib)
    teardown_attribs = classmethod(teardown_attribs)

    def setup_pootleserver(cls):
        """Sets up a Pootle server, and a session on it"""
        cls.server = pootle.PootleServer(cls.prefs.Pootle, cls.webserver)
        cls.server.name = cls.__name__
        cls.instance = cls.server.instance
        cls.session = cls.setup_session()
    setup_pootleserver = classmethod(setup_pootleserver)

    def setup_webserver(cls):
        """setup the webserver that will be used for the tests"""
        return simplewebserver.DummyServer()
    setup_webserver = classmethod(setup_webserver)

    def setup_session(cls):
        """sets up the session for the test"""
        session = users.PootleSession(sessioncache, cls.server)
        timestamp = dates.formatdate(dates.currentdate(), '%Y%m%d%H%M%S')
        session.create("admin","",timestamp,'en')
        session.remote_ip = "unit tests..."
        return session
    setup_session = classmethod(setup_session)

    def make_initial_prefs(cls):
        return prefs.PrefsParser()
    make_initial_prefs = classmethod(make_initial_prefs)

    def make_prefs(cls):
        prefs = cls.make_initial_prefs()
        prefs.setvalue('importmodules.pootle', 'Pootle.pootle')
        prefs.setvalue('Pootle.serverclass', 'pootle.PootleServer')
        instance = prefs.Pootle
        instance.sessionkey = 'change'
        instance.errorfile = os.path.join(cls.testdir, "pootle_unittest-%s-errors.log" % cls.__name__)
        instance.tracefile = os.path.join(cls.testdir, "pootle_unittest-%s-trace.log" % cls.__name__)
        prefs.setvalue("Pootle.languages.zxx.fullname", "Test Language")
        prefs.setvalue("Pootle.projects.testproject.fullname", "Pootle Unit Tests")
        prefs.setvalue("Pootle.projects.testproject.description", "Test Project for verifying functionality")
        prefs.setvalue("Pootle.projects.testproject.localfiletype", "po")
        prefs.setvalue("Pootle.users.testuser.activated", 1)

        # Need the path to the database here.  This should be in an external config file.
        prefs.setvalue("Pootle.stats.connect.database", "./tests_stats.db")
        prefs.setvalue("Pootle.hash", "allow")

        testuserprefs = instance.users.testuser
        testuserprefs.passwdhash = session.md5hexdigest("")
        instance.podirectory = cls.podir
        return prefs
    make_prefs = classmethod(make_prefs)

    def test_created(self):
        """test that the po directory actually exists"""
        print self.podir
        assert os.path.isdir(self.podir)

class NoReuse(TestCreate):
    """don't reuse webserver objects between methods"""
    def setup_webserver(self):
        """setup the webserver that will be used for the tests"""
        return simplewebserver.DummyServer()

    def setup_pootleserver(self):
        """Sets up a Pootle server, and a session on it"""
        self.server = pootle.PootleServer(self.prefs.Pootle, self.webserver)
        self.server.name = self.__class__.__name__
        self.instance = self.server.instance
        self.session = self.setup_session()

    def setup_session(self):
        """sets up the session for the test"""
        session = users.PootleSession(sessioncache, self.server)
        timestamp = dates.formatdate(dates.currentdate(), '%Y%m%d%H%M%S')
        session.create(u"admin","",timestamp,'en')
        session.remote_ip = "unit tests..."
        return session

    def setup_method(self, method):
        """sets up a webserver and jlogbookserver for this method"""
        self.webserver = self.setup_webserver()
        self.setup_testdir()
        self.setup_pootleserver()

    def teardown_method(self, method):
        """sets up a webserver and jlogbookserver for this method"""
        self.server = None
        self.instance = None
        self.logtable = None
        self.session = None
        self.webserver = None
        self.teardown_testdir()

