#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2012 Zuza Software Foundation
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
import re

from distutils.command.build import build as DistutilsBuild

from setuptools import find_packages, setup

from pootle.__version__ import sver as pootle_version


def parse_requirements(file_name):
    """Parses a pip requirements file and returns a list of packages.

    Use the result of this function in the ``install_requires`` field.
    Copied from cburgmer/pdfserver.
    """
    requirements = []
    for line in open(file_name, 'r').read().split('\n'):
        if re.match(r'(\s*#)|(\s*$)', line):
            continue
        if re.match(r'\s*-e\s+', line):
            requirements.append(re.sub(r'\s*-e\s+.*#egg=(.*)$', r'\1', line))
        elif re.match(r'\s*-f\s+', line):
            pass
        else:
            requirements.append(line)

    return requirements


class PootleBuildMo(DistutilsBuild):

    def build_mo(self):
        """Compile .mo files from available .po files"""
        import subprocess
        import gettext
        from translate.storage import factory

        print "Preparing localization files"
        pootle_po = glob.glob(os.path.join('pootle', 'locale', '*',
                                           'pootle.po'))
        pootle_js_po = glob.glob(os.path.join('pootle', 'locale', '*',
                                           'pootle_js.po'))
        for po_filename in pootle_po + pootle_js_po:
            lang = os.path.split(os.path.split(po_filename)[0])[1]
            lang_dir = os.path.join('pootle', 'locale', lang, 'LC_MESSAGES')

            if po_filename in pootle_po:
                mo_filename = os.path.join(lang_dir, 'django.mo')
            else:
                mo_filename = os.path.join(lang_dir, 'djangojs.mo')

            try:
                store = factory.getobject(po_filename)
                gettext.c2py(store.getheaderplural()[1])
            except Exception, e:
                print "skipping %s, probably invalid header: %s" % (lang, e)

            try:
                if not os.path.exists(lang_dir):
                    os.makedirs(lang_dir)
                print "compiling %s language" % lang
                subprocess.Popen(['msgfmt', '-c', '--strict', '-o', mo_filename, po_filename])
            except Exception, e:
                print "skipping %s, running msgfmt failed: %s" % (lang, e)

    def run(self):
        self.build_mo()


setup(
    name="Pootle",
    version=pootle_version,

    description="An online collaborative localization tool.",
    long_description=open(
        os.path.join(os.path.dirname(__file__), 'README.rst')
    ).read(),

    author="Translate.org.za",
    author_email="dev@translate.org.za",
    license="GNU General Public License (GPL)",
    url="http://pootle.translatehouse.org",
    download_url="http://sourceforge.net/projects/translate/files/Pootle/",

    install_requires=parse_requirements('requirements/base.txt'),
    # Remove this once Translate Toolkit is available on PyPi
    dependency_links=[
        'http://github.com/translate/translate/tarball/master#egg=translate-1.10'
    ],

    platforms=["any"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Unix",
        "Programming Language :: JavaScript",
        "Programming Language :: Python",
        "Topic :: Software Development :: Localization",
        "Topic :: Text Processing :: Linguistic"
    ],
    zip_safe=False,
    packages=find_packages(exclude=['deploy*']),
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'pootle = pootle.manage:main',
        ],
    },
    cmdclass={
        'build_mo': PootleBuildMo
    },
)
