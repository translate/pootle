#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007 Zuza Software Foundation, WordForge Foundation
#
# This is free software; you can redistribute it and/or modify
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""A Spell Checking server

The server will use the Google spell checker for languages supported by Google
otherwise it will use spell checkers provided by the enchant spell checker 
broker.

Enchant is used so that any of the enchant supported spell checker engines can 
be used.  Currently this includes: ispell, aspell, myspell/hunspell and others.

This server follows the Google spell checker protocol as used by the Google
toolbar.  The XML based protocol is documented in L{spell.SpellRequest} 
and L{spell.SpellResult}
"""

import spell
import lang
import optparse
from cherrypy import wsgiserver
import socket
import __version__

class TooLarge(Exception): 
    """Query was too large
    """
    pass

class SpellServer:
    """Spelling Server using the Google protocol

    @todo: allow a query to get back the languages available
    @todo: allow update of a pwl (ideal for supplying new words to the checker teams)
    @todo: allow user to override Google API uages and choose Enchant first
    @todo: remove the useGoogle useEnchant messiness (mostly done but needs some magic to remove the if then stuff)
    @todo: look at CherryPy to see if we can present the AJAX based forms as 
        part of the server if a user browsed to the server
    @todo: better language detection
    @todo: language fallback en_ZA->en_GB->en af_ZA->af or even af->af_ZA
    @todo: logging (at various levels: connections, languages, words requested, errors found, etc)
    """
    def __init__(self, pwldir=None):
        self._pwldir = pwldir

    def _getlang(self):
        """The spell check language requested.

        @rtype: string
        @return: the spell check language [default English (en)]
        """
        requestlang = self._environ['QUERY_STRING'].replace("lang=", "")

        if len(requestlang) == 2 or (len(requestlang) == 5 
                and requestlang[2] == "_"):
            return requestlang
        else:
            return "en"

    def _getpostdata(self):
        """The raw L{spell.SpellRequest}

        @rtype: SpellRequest
        @return: A spelling request
        """
        data_len = int(self._environ.get('HTTP_CONTENT_LENGTH', 0))
        if data_len > 30000:
            raise TooLarge
        data = self._environ.get("wsgi.input").read(data_len)
        return spell.SpellRequest(data, self._getlang())

    def __call__(self, environ, start_response):
        self._environ = environ
        try:
            request = self._getpostdata()
        except socket.timeout:
            print "Socket timeout error"
            start_response('502 BAD GATEWAY', 
                    [('Content-Type', 'text/html; charset=%s' % "utf-8")])
            return "Error"
        except TooLarge:
            start_response('502 BAD GATEWAY', 
                    [('Content-Type', 'text/html; charset=%s' % "utf-8")])
            return "Error: Too large"

        start_response('200 OK', 
                [('Content-Type', 'text/html; charset=%s' % "utf-8")])

        #if self._environ['PATH_INFO'].find("/") == 0:
        if self._getlang() in spell.GoogleChecker.langs():
            speller = spell.GoogleChecker(request, self._pwldir)
        elif self._getlang() in spell.EnchantChecker.langs():
            speller = spell.EnchantChecker(request, self._pwldir)
        else:
            return "No spell checker for that language"
        return str(speller.check())
        #return "Not found"

class Languages:
    """List all languages served from this SpellServer
    """
    def _getpostdata(self):
        """The raw L{spell.SpellRequest}

        @rtype: SpellRequest
        @return: A spelling request
        """
        data_len = int(self._environ.get('HTTP_CONTENT_LENGTH', 0))
        if data_len > 30000:
            raise TooLarge
        data = self._environ.get("wsgi.input").read(data_len)
        return data

    def __call__(self, environ, start_response):
        self._environ = environ
        try:
            request = self._getpostdata()
        except socket.timeout:
            print "Socket timeout error"
            start_response('502 BAD GATEWAY', 
                    [('Content-Type', 'text/html; charset=%s' % "utf-8")])
            return "Error"
        except TooLarge:
            start_response('502 BAD GATEWAY', 
                    [('Content-Type', 'text/html; charset=%s' % "utf-8")])
            return "Error: Too large"

        start_response('200 OK', 
                [('Content-Type', 'text/html; charset=%s' % "utf-8")])

        if self._environ['PATH_INFO'].find("/") == 0:
            return str(lang.LangResult())
        return "Not found"

class AddtoPWL:
    """Add a word to the servers Personal Word List

    The server does not use the PWL but it would allow users to contribute 
    corrections.  The client side coomponent should store the real PWL.  This
    service simply allows the data to be stored in both places and for the
    server-side PWL to act as input for missing words in the spell checker.
    """
    pass

def main():
    """Start the Spell Checking server with command line options
    """
    parser = optparse.OptionParser(version="%prog "+
            __version__.ver, description="Spell checking server")
    defaultport = 8008
    parser.add_option("-p", "--port", dest="port", default=defaultport,
            metavar="PORT", type="int",
            help="server port [default: %i]" % defaultport)
    parser.add_option("", "--pwl", dest="pwldir", 
            metavar="PWLDIR", type="string",
            help="personal word list directory")
    (options, args) = parser.parse_args()
    server = wsgiserver.CherryPyWSGIServer(('', options.port), 
            [('/', SpellServer(options.pwldir)), ('/lang', Languages())])
    try:
        print "Server started on port %s" % options.port
        server.start()
    except KeyboardInterrupt:
        server.stop()
        print "Server stopped"

if __name__ == "__main__":
    main()
