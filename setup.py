#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import glob
import os
import re
import sys

from distutils import log
from distutils.core import Command
from distutils.command.build import build as DistutilsBuild
from distutils.errors import DistutilsOptionError

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

from pootle import __version__


def parse_requirements(file_name):
    """Parses a pip requirements file and returns a list of packages.

    Use the result of this function in the ``install_requires`` field.
    Copied from cburgmer/pdfserver.
    """
    requirements = []
    for line in open(file_name, 'r').read().split('\n'):
        # Ignore comments, blank lines and included requirements files
        if re.match(r'(\s*#)|(\s*$)|((-r|--allow-external|--allow-unverified) .*$)', line):
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


class BuildChecksTemplatesCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import django
        import codecs
        from pootle.apps.pootle_misc.checks import check_names, excluded_filters
        from translate.filters.checks import (TeeChecker,
                                              StandardChecker, StandardUnitChecker)
        try:
            from docutils.core import publish_parts
        except ImportError:
            from distutils.errors import DistutilsModuleError
            raise DistutilsModuleError("Please install the docutils library.")
        from pootle import syspath_override
        django.setup()

        def get_check_description(name, filterfunc):
            """Get a HTML snippet for a specific quality check description.

            The quality check description is extracted from the check function
            docstring (which uses reStructuredText) and rendered using docutils
            to get the HTML snippet.
            """
            # Provide a header with an anchor to refer to.
            description = ('\n<h3 id="%s">%s</h3>\n\n' %
                           (name, unicode(check_names[name])))

            # Clean the leading whitespace on each docstring line so it gets
            # properly rendered.
            docstring = "\n".join(line.strip() for line in filterfunc.__doc__.split("\n"))

            # Render the reStructuredText in the docstring into HTML.
            description += publish_parts(docstring, writer_name="html")["body"]
            return description

        print("Regenerating Translate Toolkit quality checks descriptions")

        # Get a checker with the Translate Toolkit checks. Note that filters
        # that are not used in Pootle are excluded.
        fd = TeeChecker(
            checkerclasses=[StandardChecker, StandardUnitChecker]
        ).getfilters(excludefilters=excluded_filters)

        docs = sorted(
            get_check_description(name, f) for name, f in fd.items()
        )

        # Output the quality checks descriptions to the HTML file.
        templates_dir = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "pootle", "templates"
        )
        filename = os.path.join(templates_dir, "help/_ttk_quality_checks.html")

        with codecs.open(filename, "w", "utf-8") as f:
            f.write(u"\n".join(docs))

        print("Checks templates written to %r" % (filename))


setup(
    name="Pootle",
    version=__version__,

    description="An online collaborative localization tool.",
    long_description=open(
        os.path.join(os.path.dirname(__file__), 'README.rst')
    ).read(),

    author="Translate",
    author_email="dev@translate.org.za",
    license="GNU General Public License 3 or later (GPLv3+)",
    url="http://pootle.translatehouse.org",
    download_url="https://github.com/translate/pootle/releases/tag/" + __version__,

    install_requires=parse_requirements('requirements/base.txt'),
    tests_require=parse_requirements('requirements/tests.txt'),

    platforms=["any"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
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
        'build_checks_templates': BuildChecksTemplatesCommand,
        'build_mo': PootleBuildMo,
        'test': PyTest,
    },
)
