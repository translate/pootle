#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import re
import sys
from distutils import log
from distutils.command.build import build as DistutilsBuild
from distutils.core import Command
from distutils.errors import DistutilsOptionError

from pkg_resources import parse_version, require
from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

from pootle import __version__
from pootle.constants import DJANGO_MINIMUM_REQUIRED_VERSION


def check_pep440_versions():
    if require('setuptools')[0].parsed_version < parse_version('8.0'):
        exit("setuptools %s is incompatible with Pootle. Please upgrade "
             "using:\n"
             "'pip install --upgrade setuptools'"
             % require('setuptools')[0].version)
    if require('pip')[0].parsed_version < parse_version('6.0'):
        exit("pip %s is incompatible with Pootle. Please upgrade "
             "using:\n"
             "'pip install --upgrade pip'" % require('pip')[0].version)


def parse_requirements(file_name, recurse=False):
    """Parses a pip requirements file and returns a list of packages.

    Use the result of this function in the ``install_requires`` field.
    Copied from cburgmer/pdfserver.
    """
    requirements = []
    for line in open(file_name, 'r').read().split('\n'):
        # Ignore comments, blank lines and included requirements files
        if re.match(r'(\s*#)|(\s*$)|'
                    '((--allow-external|--allow-unverified) .*$)', line):
            continue
        if re.match(r'-r .*$', line):
            if recurse:
                requirements.extend(parse_requirements(
                    'requirements/' +
                    re.sub(r'-r\s*(.*[.]txt)$', r'\1', line), recurse))
            continue

        if re.match(r'\s*-e\s+', line):
            requirements.append(re.sub(
                r'''\s*-e\s+          # -e marker
                 .*                   # URL
                 \#egg=               # egg marker
                 ([^\d]*)-            # \1 dep name
                 ([\.\d]*             # \2 M.N.*
                 ((a|b|rc|dev)+\d*)*  # (optional) devN
                 )$''',
                r'\1==\2', line, flags=re.VERBOSE))
            log.warn("Pootle requires a non-PyPI dependency, when using pip "
                     "ensure you use the --process-dependency-links option.")
        elif re.match(r'\s*-f\s+', line):
            pass
        else:
            requirements.append(line)

    return requirements


def parse_dependency_links(file_name, recurse=False):
    dependency_links = []
    for line in open(file_name, 'r').read().split('\n'):
        if re.match(r'\s*-e\s+', line):
            dependency_links.append(re.sub(r'\s*-e\s+', '', line))

        if re.match(r'-r .*$', line):
            if recurse:
                dependency_links.extend(parse_dependency_links(
                    'requirements/' +
                    re.sub(r'-r\s*(.*[.]txt)$', r'\1', line), recurse))
            continue

    return dependency_links


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['--tb=short', 'tests/']
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
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
        ('check', None,
         "check for errors"),
    ]
    boolean_options = ['all']

    po_path_base = os.path.join('pootle', 'locale')
    _langs = []

    def initialize_options(self):
        self.all = False
        self.lang = None
        self.check = False

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

        error_occured = False

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
                if self.check:
                    command = ['msgfmt', '-c', '--strict',
                               '-o', mo_filename, po_filename]
                else:
                    command = ['msgfmt', '--strict',
                               '-o', mo_filename, po_filename]
                try:
                    subprocess.check_call(command, stderr=subprocess.STDOUT)
                except subprocess.CalledProcessError as e:
                    error_occured = True
                except Exception as e:
                    log.warn("%s: skipping, running msgfmt failed: %s",
                             lang, e)

                try:
                    store = factory.getobject(po_filename)
                    gettext.c2py(store.getheaderplural()[1])
                except Exception:
                    log.warn("%s: invalid plural header in %s",
                             lang, po_filename)

        if error_occured:
            sys.exit(1)

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
        from pootle.apps.pootle_misc.checks import (check_names,
                                                    excluded_filters)
        from translate.filters.checks import (TeeChecker, StandardChecker,
                                              StandardUnitChecker)
        try:
            from docutils.core import publish_parts
        except ImportError:
            from distutils.errors import DistutilsModuleError
            raise DistutilsModuleError("Please install the docutils library.")
        from pootle import syspath_override  # noqa
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
            docstring = "\n".join(line.strip()
                                  for line in filterfunc.__doc__.split("\n"))

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


check_pep440_versions()


dependency_links = []

install_requires = parse_requirements('requirements/base.txt'),
dependency_links += parse_dependency_links('requirements/base.txt')

tests_require = parse_requirements('requirements/tests.txt'),
dependency_links += parse_dependency_links('requirements/tests.txt')

extras_require = {}
extras_require['dev'] = parse_requirements('requirements/dev.txt', recurse=True)
dependency_links += parse_dependency_links('requirements/dev.txt', recurse=True)
# Database dependencies
extras_require['mysql'] = parse_requirements('requirements/_db_mysql.txt')
dependency_links += parse_dependency_links('requirements/_db_mysql.txt')
extras_require['postgresql'] = parse_requirements('requirements/_db_postgresql.txt')
dependency_links += parse_dependency_links('requirements/_db_postgresql.txt')
# Pootle FS plugins
extras_require['git'] = parse_requirements('requirements/_pootle_fs_git.txt')
dependency_links += parse_dependency_links('requirements/_pootle_fs_git.txt')
# Markdown
extras_require['markdown'] = parse_requirements('requirements/_markup_markdown.txt')
dependency_links += parse_dependency_links('requirements/_markup_markdown.txt')
# Testing
extras_require['travis'] = parse_requirements('requirements/travis.txt',
                                              recurse=True)
dependency_links += parse_dependency_links('requirements/travis.txt',
                                           recurse=True)
extras_require['appveyor'] = parse_requirements('requirements/appveyor.txt',
                                                recurse=True)
dependency_links += parse_dependency_links('requirements/appveyor.txt',
                                           recurse=True)


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
    download_url="https://github.com/translate/pootle/releases/tag/" +
        __version__,

    install_requires=install_requires,
    dependency_links=dependency_links,
    tests_require=tests_require,

    extras_require=extras_require,

    platforms=["any"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: %s"
            % ".".join(map(str, DJANGO_MINIMUM_REQUIRED_VERSION[:2])),
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: "
        "GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Operating System :: Unix",
        "Programming Language :: JavaScript",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Localization",
        "Topic :: Text Processing :: Linguistic"
    ],
    zip_safe=False,
    packages=find_packages(),
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
