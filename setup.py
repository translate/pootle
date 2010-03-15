#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
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

import glob
import os
import os.path as path
import re
from distutils import util
from distutils.command.build import build as DistutilsBuild
from distutils.command.install import install as DistutilsInstall
from distutils.core import setup

from pootle.__version__ import sver as pootle_version


###############################################################################
# CONSTANTS
###############################################################################

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Web Environment",
    "Intended Audience :: Developers",
    "Intended Audience :: End Users/Desktop",
    "Intended Audience :: Information Technology",
    "License :: OSI Approved :: GNU General Public License (GPL)",
    "Programming Language :: Python",
    "Topic :: Software Development :: Localization",
    "Topic :: Text Processing :: Linguistic"
    "Operating System :: OS Independent",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: Unix"
]
pootle_description="An online collaborative localization tool."
pootle_description_long="""Pootle is used to create program translations.

It uses the Translate Toolkit to get access to translation files and therefore
can edit a variety of files (including PO and XLIFF files)."""

INSTALL_CONFIG_DIR = '/etc/pootle'
INSTALL_DATA_DIR = 'share/pootle'
INSTALL_DOC_DIR = 'share/doc/pootle'
INSTALL_WORKING_DIR = '/var/lib/pootle'

###############################################################################
# HELPER FUNCTIONS
###############################################################################

def collect_options():
    data_files = [
        (INSTALL_CONFIG_DIR, ['localsettings.py']),
        (INSTALL_DOC_DIR, ['wsgi.py', 'ChangeLog', 'COPYING', 'README', 'INSTALL']),
        (INSTALL_WORKING_DIR + '/dbs', []) # Create the empty "dbs" dir
    ] + list_tree(INSTALL_DATA_DIR, 'templates') + list_tree(INSTALL_DATA_DIR, 'html') + \
        list_tree(INSTALL_WORKING_DIR, 'po') + list_tree(INSTALL_DATA_DIR, 'mo')

    packages = ['pootle'] + ['pootle.' + pkg for pkg in find_packages('pootle')] + \
            find_packages('local_apps') + find_packages('external_apps')
    package_data = {
        '':           ['*.html', '*.txt', '*.xml', '*.css', '*.js'],
        'pootle_app': expand_tree_globs('local_apps/pootle_app', ['templates'], ['*.html']),
        'pootle_notifications': expand_tree_globs('local_apps/pootle_notifications', ['templates'], ['*.html']),
        'djblets':    expand_tree_globs('external_apps/djblets', ['siteconfig', 'util'], ['*.html']),
    }
    package_dir = {
        'pootle_app':   'local_apps/pootle_app',
        'pootle_autonotices': 'local_apps/pootle_autonotices',
        'pootle_language': 'local_apps/pootle_language',
        'pootle_misc':  'local_apps/pootle_misc',
        'pootle_notifications': 'local_apps/pootle_notifications',
        'pootle_profile': 'local_apps/pootle_profile',
        'pootle_project': 'local_apps/pootle_project',
        'pootle_statistics': 'local_apps/pootle_statistics',
        'pootle_store': 'local_apps/pootle_store',
        'pootle_terminology': 'local_apps/pootle_terminology',
        'pootle_translationproject': 'local_apps/pootle_translationproject',
        'registration': 'external_apps/registration',
        'profiles':     'external_apps/profiles',
        'djblets':      'external_apps/djblets',
    }
    scripts = ['import_pootle_prefs', 'updatetm', 'PootleServer']
    options = {
        'data_files':   data_files,
        'packages':     packages,
        'package_data': package_data,
        'package_dir':  package_dir,
        'scripts':      scripts,
    }
    return options

def expand_tree_globs(root, subdirs, globs):
    if root.endswith('/'):
        root = root[:-1]

    dirglobs = []
    for subdir in subdirs:
        for g in globs:
            if glob.glob(path.join(root, subdir, g)):
                dirglobs.append(path.join(subdir, g))

        for dirpath, dirs, files in os.walk(path.join(root, subdir)):
            curdir = dirpath[len(root)+1:]
            for d in dirs:
                for g in globs:
                    if glob.glob(path.join(root, curdir, d, g)):
                        dirglobs.append(path.join(curdir, d, g))
    return dirglobs

# The function below was shamelessly copied from setuptools
def find_packages(where='.', exclude=()):
    """Return a list all Python packages found within directory 'where'

    'where' should be supplied as a "cross-platform" (i.e. URL-style) path; it
    will be converted to the appropriate local path syntax.  'exclude' is a
    sequence of package names to exclude; '*' can be used as a wildcard in the
    names, such that 'foo.*' will exclude all subpackages of 'foo' (but not
    'foo' itself).
    """
    from distutils.util import convert_path
    out = []
    stack=[(convert_path(where), '')]
    while stack:
        where,prefix = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where,name)
            if ('.' not in name and os.path.isdir(fn) and
                os.path.isfile(os.path.join(fn,'__init__.py'))
            ):
                out.append(prefix+name); stack.append((fn,prefix+name+'.'))
    for pat in list(exclude)+['ez_setup']:
        from fnmatch import fnmatchcase
        out = [item for item in out if not fnmatchcase(item,pat)]
    return out

def list_tree(target_base, root):
    tree = []
    headlen = -1
    for dirpath, dirs, files in os.walk(root):
        if headlen < 0:
            headlen = len(dirpath) - len(root)
        dirpath = dirpath[headlen:]
        tree.append((
            path.join(target_base, dirpath),
            [path.join(dirpath, f) for f in files]
        ))

    return tree


###############################################################################
# CLASSES
###############################################################################

class PootleBuildMo(DistutilsBuild):
    def build_mo(self):
        """Compile .mo files from available .po files"""
        import subprocess
        import gettext
        from translate.storage import factory

        print "Preparing localization files"
        for po_filename in glob.glob(path.join('po', 'pootle', '*', 'pootle.po')):
            lang = path.split(path.split(po_filename)[0])[1]
            lang_dir = path.join('mo', lang, 'LC_MESSAGES')
            mo_filename = path.join(lang_dir, 'django.mo')

            try:
                store = factory.getobject(po_filename)
                gettext.c2py(store.getheaderplural()[1])
                if not path.exists(lang_dir):
                    os.makedirs(lang_dir)
                print "compiling %s language" % lang
                subprocess.Popen(['msgfmt', '-c', '--strict', '-o', mo_filename, po_filename])
            except Exception, e:
                print "skipping %s, probably invalid header: %s" % (lang, e)

    def run(self):
        self.build_mo()


class PootleBuild(DistutilsBuild):
    """make sure build_mo is run when build is run"""
    def run(self):
        DistutilsBuild.run(self)


class PootleInstall(DistutilsInstall):
    def run(self):
        DistutilsInstall.run(self)
        self.update_install_dirs_py()

    def update_install_dirs_py(self):
        # Get the right target location of install_dirs.py, depending on
        # whether --root or --prefix was specified
        install_dirs_py_path = path.abspath(path.join(self.install_lib, 'pootle', 'install_dirs.py'))

        if not path.isfile(install_dirs_py_path):
            raise Exception('install_dirs.py file should exist, but does not. o_O (%s)' % (install_dirs_py_path))
        conf_dir = path.abspath(path.join(self.install_base, INSTALL_CONFIG_DIR))
        data_dir = path.abspath(path.join(self.install_base, INSTALL_DATA_DIR))
        work_dir = path.abspath(path.join(self.install_base, INSTALL_WORKING_DIR))

        #if self.root:
        #    # We use distutils.util.change_root, because INSTALL_CONFIG_DIR
        #    # and INSTALL_WORKING_DIR are absolute paths and stays that way when
        #    # used with os.path.join() as above. This also means that data_dir
        #    # should be changed here if the value # of INSTALL_DATA_DIR becomes
        #    # an absolute path.
        #    conf_dir = util.change_root(self.root, INSTALL_CONFIG_DIR)
        #    work_dir = util.change_root(self.root, INSTALL_WORKING_DIR)

        # Replace directory variables in settings.py to reflect the current installation
        lines = open(install_dirs_py_path).readlines()
        config_re = re.compile(r'^CONFIG_DIR\s*=')
        datadir_re = re.compile(r'^DATA_DIR\s*=')
        workdir_re = re.compile(r'^WORKING_DIR\s*=')

        for i in range(len(lines)):
            if config_re.match(lines[i]):
                lines[i] = "CONFIG_DIR = '%s'\n" % (conf_dir)
            elif datadir_re.match(lines[i]):
                lines[i] = "DATA_DIR = '%s'\n" % (data_dir)
            elif workdir_re.match(lines[i]):
                lines[i] = "WORKING_DIR = '%s'\n" % (work_dir)
        open(install_dirs_py_path, 'w').write(''.join(lines))


###############################################################################
# MAIN
###############################################################################
if __name__ == '__main__':
    setup(
        name="Pootle",
        version=pootle_version,
        license="GNU General Public License (GPL)",
        description=pootle_description,
        long_description=pootle_description_long,
        author="Translate.org.za",
        author_email="translate-devel@lists.sourceforge.net",
        url="http://translate.sourceforge.net/wiki/pootle/index",
        download_url="http://sourceforge.net/projects/translate/files/Pootle/",
        install_requires=["translate-toolkit>=1.5.0", "Django>=1.0"],
        platforms=["any"],
        classifiers=classifiers,
        cmdclass={'install': PootleInstall, 'build': PootleBuild, 'build_mo': PootleBuildMo},
        **collect_options()
    )
