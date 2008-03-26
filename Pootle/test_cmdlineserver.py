#!/usr/bin/env python

"""Server environment for testing simplewebserver (command line web server)
This uses the basic environment from test_create and runs a web server in a separate thread
The top-level tests are then in test_client / test_ie / test_mozilla etc
These can then be layered on top of this server"""

from Pootle import test_create
from jToolkit.web import simplewebserver
from jToolkit import errors
import urllib2
import time

class TestCmdlineServer(test_create.NoReuse):
    # this is called from setup_class in test_create.TestCreate
    def setup_webserver(self):
        """setup the webserver that will be used for the tests"""
        print "setting up web server"
        webserverclass = simplewebserver.jToolkitHTTPServer(simplewebserver.ThreadedHTTPServer)
        options = simplewebserver.WebOptionParser().parse_args([])[0]
        options.port = 0
        options.servertype = 'standard'
        errorhandler = errors.ConsoleErrorHandler()
        webserver = webserverclass(options, errorhandler)
        return webserver

    def setup_method(self, method):
        """starts a new simplewebserver in a separate thread"""
        try:
            test_create.NoReuse.setup_method(self, method)
        except Exception, e:
            print "exception in test_create setup_method:", e
            test_create.NoReuse.teardown_method(self, method)
            raise
        print "finished setup_method phase 1"
        # self.webserver.options.port = self.port
        self.baseaddress = "http://%s:%d/" % (self.webserver.hostname, self.webserver.port)
        ThreadClass = self.webserver.ThreadClass
        self.webserverthread = ThreadClass(target = simplewebserver.run, name="webserver", args=(self.server, self.webserver.options))
        self.webserverthread.start()
        # wait until it actually is started
        waited = 0.0
        sleep = 0.001
        maxwait = 3.0
        while not hasattr(self.webserver, "stop"):
            time.sleep(sleep)
            waited += sleep
            if sleep > maxwait:
                raise RuntimeError("webserver failed to start in %0.1f seconds" % maxwait)

    def teardown_method(self, method):
        """close the web server for this method"""
        try:
            self.server.sessioncache.clear()
            self.webserver.setstop(True)
            # ping the webserver to make it stop
            waited = 0.0
            sleep = 0.05
            max_wait = 5.0
            while self.webserverthread.isAlive():
                time.sleep(sleep)
                if not self.webserverthread.isAlive():
                    break
                # if the webserver is sleeping a request should wake it up...
                # try:
                #     x = urllib2.urlopen(self.baseaddress)
                # except Exception, e:
                #     pass
                waited += sleep
                sleep += 0.05
                if waited >= max_wait:
                    raise RuntimeError("webserver failed to stop in %0.1f seconds" % (waited))
	finally:
            test_create.NoReuse.teardown_method(self, method)

