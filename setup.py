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
from pootle.core.utils import version


README_FILE = 'README.rst'


def check_pep440_versions():
    if require('setuptools')[0].parsed_version < parse_version('18.5'):
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

        if re.match(r'^\s*-e\s+', line):
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
        if re.match(r'^\s*-e\s+', line):
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


class PootleUpdateReadme(Command):
    """Process a README file for branching"""

    user_options = [
        ('write', 'w', 'Overwrite the %s file' % README_FILE),
        ('branch', 'b', 'Rewrite using branch rewriting (default)'),
        ('release', 'r', 'Rewrite using release or tag rewriting'),
        # --check - to see that README is what is expected
    ]
    description = "Update the %s file" % README_FILE

    def initialize_options(self):
        self.write = False
        self.branch = True
        self.release = False

    def finalize_options(self):
        if self.release:
            self.branch = False

    def run(self):
        new_readme = parse_long_description(README_FILE, self.release)
        if self.write:
            with open(README_FILE, 'w') as readme:
                readme.write(new_readme)
        else:
            print(new_readme)


class BuildChecksTemplatesCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import django
        import codecs
        from pootle.apps.pootle_checks.constants import (
            CHECK_NAMES, EXCLUDED_FILTERS)
        from translate.filters.checks import (TeeChecker, StandardChecker,
                                              StandardUnitChecker)
        from translate.lang.factory import get_all_languages
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
                           (name, unicode(CHECK_NAMES[name])))

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
        checkerclasses = [StandardChecker, StandardUnitChecker]
        # Also include language-specific checks
        checkerclasses.extend([type(lang.checker)
                               for lang in get_all_languages()
                               if lang.checker is not None])
        fd = TeeChecker(
            checkerclasses=checkerclasses
        ).getfilters(excludefilters=EXCLUDED_FILTERS)

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


def parse_long_description(filename, tag=False):

    def reduce_header_level():
        # PyPI doesn't like title to be underlined with =
        if tag:
            readme_lines[1] = readme_lines[1].replace("=", "-")

    def adjust_installation_command():
        extra_options = []
        if dependency_links:
            extra_options += ["--process-dependency-links"]
        if version.is_prerelease():
            extra_options += ["--pre"]
        for ln, line in enumerate(readme_lines):
            if re.match(r'^\s*pip install\s+.*\s+Pootle$', line):
                if extra_options:
                    readme_lines[ln] = (
                        "  pip install %s Pootle\n" % " ".join(extra_options))
                else:
                    readme_lines[ln] = "  pip install Pootle\n"

    def replace_urls():
        from pootle.core.utils import version
        branch = version.get_git_branch()
        branch_escape = None
        if branch is not None:
            branch_escape = branch.replace('/', '%2F')
        for ln, line in enumerate(readme_lines):
            for pattern, replace, rewrite_type in (
                # Release Notes
                ('releases/[0-9]\.[0-9]\.[0-9]\.html',
                 'releases/%s.html' % version.get_main_version(),
                 'all'),
                # Adjust docs away from /latest/
                ('/pootle/en/latest/',
                 '/pootle/en/%s/' % version.get_rtd_version(),
                 'branch'),
                # Coverage - Codecov for branches
                ('codecov.io/gh/translate/pootle/branch/master',
                 'codecov.io/gh/translate/pootle/branch/%s' % branch_escape,
                 'branch'),
                ('shields.io/codecov/c/github/translate/pootle/master',
                 'shields.io/codecov/c/github/translate/pootle/%s' %
                 branch_escape,
                 'branch'),
                # Coverage - Coveralls for tags
                ('codecov.io/gh/translate/pootle/branch/master',
                 'coveralls.io/github/translate/pootle?branch=%s' %
                 version.get_version(),
                 'tag'),
                ('shields.io/codecov/c/github/translate/pootle/master',
                 'shields.io/coveralls/translate/pootle/%s' %
                 version.get_version(),
                 'tag'),
                # Travis - change only the badge, can't link to branch
                ('travis/translate/pootle/master',
                 'travis/translate/pootle/%s' % version.get_git_branch(),
                 'branch'),
                ('travis/translate/pootle/master',
                 'travis/translate/pootle/%s' % version.get_version(),
                 'tag'),
                # Landscape
                ('landscape.io/github/translate/pootle/master',
                 'landscape.io/github/translate/pootle/%s' %
                 version.get_git_branch(),
                 'branch'),
                # Requires.io
                ('requires/github/translate/pootle/master',
                 'requires/github/translate/pootle/%s' %
                 version.get_git_branch(),
                 'branch'),
                ('requirements/\?branch=master',
                 'requirements/?branch=%s' % branch_escape,
                 'branch'),
                ('https://img.shields.io/requires/.*',
                 'https://requires.io/github/translate/'
                 'pootle/requirements.svg?tag=%s'
                 % version.get_version(),
                 'tag'),
                ('requirements/\?branch=master',
                 'requirements/?tag=%s' % version.get_version(),
                 'tag'),
            ):
                if ((rewrite_type == 'tag' and tag)
                    or (rewrite_type == 'branch'
                        and not tag
                        and branch is not None)
                    or rewrite_type == 'all'):
                    readme_lines[ln] = re.sub(pattern, replace, readme_lines[ln])

    filename = os.path.join(os.path.dirname(__file__), filename)
    with open(filename) as f:
        readme_lines = f.readlines()
    reduce_header_level()
    adjust_installation_command()
    replace_urls()
    return "".join(readme_lines)


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
# Elasticsearch
extras_require['es1'] = parse_requirements('requirements/_es_1.txt')
dependency_links += parse_dependency_links('requirements/_es_1.txt')
extras_require['es2'] = parse_requirements('requirements/_es_2.txt')
dependency_links += parse_dependency_links('requirements/_es_2.txt')
extras_require['es5'] = parse_requirements('requirements/_es_5.txt')
dependency_links += parse_dependency_links('requirements/_es_5.txt')
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
    long_description=parse_long_description(README_FILE, tag=True),

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
        'pytest11': [
            'pytest_pootle = pytest_pootle.plugin',
        ]
    },
    cmdclass={
        'build_checks_templates': BuildChecksTemplatesCommand,
        'build_mo': PootleBuildMo,
        'update_readme': PootleUpdateReadme,
        'test': PyTest,
    },
)
