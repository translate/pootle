#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
# Copyright 2014 Evernote Corporation
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
import sys

from distutils import log
from distutils.command.build import build as DistutilsBuild
from distutils.errors import DistutilsOptionError

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

from pootle.__version__ import sver as pootle_version


def parse_requirements(file_name):
    """Parses a pip requirements file and returns a list of packages.

    Use the result of this function in the ``install_requires`` field.
    Copied from cburgmer/pdfserver.
    """
    requirements = []
    for line in open(file_name, 'r').read().split('\n'):
        # Ignore comments, blank lines and included requirements files
        if re.match(r'(\s*#)|(\s*$)|(-r .*$)', line):
            continue

        if re.match(r'\s*-e\s+', line):
            requirements.append(re.sub(r'\s*-e\s+.*#egg=(.*)$', r'\1', line))
        elif re.match(r'\s*-f\s+', line):
            pass
        else:
            requirements.append(line)

    return requirements


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['--tb=short', 'tests/']
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


class PootleBuildMo(DistutilsBuild):

    description = "compile Gettext PO files into MO"
    user_options = [
        ('all', None,
         "compile all language (don't use LINGUAS file)"),
        ('lang=', 'l',
         "specify a language to compile"),
    ]
    boolean_options = ['all']

    po_path_base = os.path.join('pootle', 'locale')
    _langs = []

    def initialize_options(self):
        self.all = False
        self.lang = None

    def finalize_options(self):
        if self.all and self.lang is not None:
            raise DistutilsOptionError(
                "Can't use --all and --lang together"
            )
        if self.lang is not None:
            self._langs = [self.lang]
        elif self.all:
            for lang in os.listdir(self.po_path_base):
                if (os.path.isdir(os.path.join(self.po_path_base, lang)) and
                    lang != "templates"):
                    self._langs.append(lang)
        else:
            for lang in open(os.path.join('pootle', 'locale', 'LINGUAS')):
                self._langs.append(lang.rstrip())

    def build_mo(self):
        """Compile .mo files from available .po files"""
        import subprocess
        import gettext
        from translate.storage import factory

        for lang in self._langs:
            lang = lang.rstrip()

            po_path = os.path.join('pootle', 'locale', lang)
            mo_path = os.path.join('pootle', 'locale', lang, 'LC_MESSAGES')

            if not os.path.exists(mo_path):
                os.makedirs(mo_path)

            for po, mo in (('pootle.po', 'django.mo'),
                           ('pootle_js.po', 'djangojs.mo')):
                po_filename = os.path.join(po_path, po)
                mo_filename = os.path.join(mo_path, mo)

                if not os.path.exists(po_filename):
                    log.warn("%s: missing file %s", lang, po_filename)
                    continue

                if not os.path.exists(mo_path):
                    os.makedirs(mo_path)

                log.info("compiling %s", lang)
                try:
                    subprocess.call([
                        'msgfmt', '--strict', '-o', mo_filename, po_filename],
                        stderr=subprocess.STDOUT)
                except Exception as e:
                    log.warn("%s: skipping, running msgfmt failed: %s",
                             lang, e)

                try:
                    store = factory.getobject(po_filename)
                    gettext.c2py(store.getheaderplural()[1])
                except Exception:
                    log.warn("%s: invalid plural header in %s",
                             lang, po_filename)

    def run(self):
        self.build_mo()


setup(
    name="Pootle",
    version=pootle_version,

    description="An online collaborative localization tool.",
    long_description=open(
        os.path.join(os.path.dirname(__file__), 'README.rst')
    ).read(),

    author="Translate",
    author_email="dev@translate.org.za",
    license="GNU General Public License (GPL)",
    url="http://pootle.translatehouse.org",
    download_url="http://sourceforge.net/projects/translate/files/Pootle/" + pootle_version,

    install_requires=parse_requirements('requirements/base.txt'),

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
            'pootle = pootle.runner:main',
        ],
    },
    cmdclass={
        'build_mo': PootleBuildMo,
        'test': PyTest,
    },
)
