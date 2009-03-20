#!/usr/bin/python
# -*- coding: utf-8 -*-
#  Copyright 2004-2009 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# translate is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# translate; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA  02111-1307  USA
#
# TODO: Make this less ugly
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'Pootle.settings'

# Import this early to force module initialization so that our
# hijacking of Django's translation machinery will work from the
# start.
from Pootle.i18n import gettext

# We don't need kid in this file, but this will show quickly if it is
# not installed.
import kid
import sys
import random
import optparse
from wsgiref.simple_server import make_server
from django.core.handlers.wsgi import WSGIHandler
from pootle_app.translation_project import scan_translation_projects
from Pootle import pootlefile, users, filelocations
from Pootle import pan_app
from Pootle.misc import prefs
from Pootle import __version__ as pootleversion
from translate import __version__ as toolkitversion


class PootleServer(object):
    """the Server that serves the Pootle Pages"""

    def __init__(self):
        self.templatedir = filelocations.templatedir

    def refreshstats(self, args):
        """refreshes all the available statistics...
        """

        if args:

            def filtererrorhandler(functionname, str1, str2, e):
                print 'error in filter %s: %r, %r, %s' % (functionname, str1,
                        str2, e)
                return False

            checkerclasses = [projects.checks.StandardChecker,
                              projects.checks.StandardUnitChecker]
            stdchecker = \
                projects.checks.TeeChecker(checkerclasses=checkerclasses,
                    errorhandler=filtererrorhandler)
            for arg in args:
                if not os.path.exists(arg):
                    print 'file not found:', arg
                if os.path.isdir(arg):
                    if not arg.endswith(os.sep):
                        arg += os.sep
                    (projectcode, languagecode) = \
                        self.potree.getcodesfordir(arg)
                    dummyproject = projects.DummyStatsProject(arg, stdchecker,
                            projectcode, languagecode)

                    def refreshdir(dummy, dirname, fnames):
                        reldirname = dirname.replace(dummyproject.podir, '')
                        for fname in fnames:
                            fpath = os.path.join(reldirname, fname)
                            fullpath = os.path.join(dummyproject.podir, fpath)
                            # TODO: PO specific
                            if fname.endswith('.po')\
                                 and not os.path.isdir(fullpath):
                                if not os.path.exists(fullpath):
                                    print 'file does not exist:', fullpath
                                    return
                                print 'refreshing stats for', fpath
                                pootlefile.pootlefile(dummyproject,
                                        fpath).statistics.updatequickstats()

                    os.path.walk(arg, refreshdir, None)
                elif os.path.isfile(arg):
                    dummyproject = projects.DummyStatsProject('.', stdchecker)
                    print 'refreshing stats for', arg
                    projects.pootlefile.pootlefile(dummyproject, arg)
        else:
            print 'refreshing stats for all files in all projects'
            self.potree.refreshstats()


class PootleOptionParser(optparse.OptionParser):

    def __init__(self):
        versionstring = \
            '''%%prog %s
Translate Toolkit %s
Kid %s
Python %s (on %s/%s)''' % (
            pootleversion.ver,
            toolkitversion.sver,
            kid.__version__,
            sys.version,
            sys.platform,
            os.name,
            )
        optparse.OptionParser.__init__(self)
        self.set_default('prefsfile', filelocations.prefsfile)
        self.set_default('instance', 'Pootle')
        self.set_default('htmldir', filelocations.htmldir)
        self.add_option(
            '',
            '--refreshstats',
            dest='action',
            action='store_const',
            const='refreshstats',
            default='runwebserver',
            help='refresh the stats files instead of running the webserver',
            )
        self.add_option(
            '',
            '--no_cache_templates',
            action='store_false',
            dest='cache_templates',
            default=True,
            help='Pootle should not cache templates, but reload them with every request.'
                ,
            )
        self.add_option(
            '',
            '--port',
            action='store',
            type='int',
            dest='port',
            default='8080',
            help='The TCP port on which the server should listen for new connections.'
                ,
            )


def checkversions():
    """Checks that version dependencies are met
    """

    if not hasattr(toolkitversion, 'build') or toolkitversion.build < 12000:
        raise RuntimeError('requires Translate Toolkit version >= 1.2.  Current installed version is: %s'
                            % toolkitversion.sver)


def set_template_caching(options):
    if options.cache_templates is not None:
        pan_app.cache_templates = options.cache_templates


def set_options(options):
    pan_app.prefs = prefs.load_preferences(options.prefsfile)
    set_template_caching(options)


def run_pootle(options, args):
    pan_app.pootle_server = PootleServer()
    if options.action == 'runwebserver':
        httpd = make_server('', options.port, WSGIHandler())
        httpd.serve_forever()
    elif options.action == 'refreshstats':
        pan_app.pootle_server.refreshstats(args)


def init_db():
    from django.core.management import call_command
    from pootle_app.profile import PootleProfile
    try:
        # If this raises an exception, it means that the database
        # tables don't yet exist
        PootleProfile.objects.count()
    except:
        call_command('syncdb')
        # If there are no profiles, then we haven't populated our
        # database yet. So do it!
    if PootleProfile.objects.count() == 0:
        call_command('initdb')


def main():
    # run the web server
    init_db()
    gettext.unbootstrap()
    checkversions()
    parser = PootleOptionParser()
    (options, args) = parser.parse_args()
    if options.action != 'runwebserver':
        options.servertype = 'dummy'
    set_options(options)
    scan_translation_projects()
    run_pootle(options, args)


if __name__ == '__main__':
    main()
