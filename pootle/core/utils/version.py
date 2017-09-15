# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

# Some functions are taken from or modelled on the version management in
# Django.  Those are:
# Copyright (c) Django Software Foundation and individual contributors.  All
# rights reserved.

from __future__ import print_function

import datetime
import os
import subprocess

try:
    from django.utils.lru_cache import lru_cache
except ImportError:
    # Required for Python 2.7 support and when backported Django version is
    # unavailable
    def lru_cache():
        def fake(func):
            return func
        return fake

from pootle.constants import VERSION


CANDIDATE_MARKERS = ('alpha', 'beta', 'rc', 'final')


def get_version(version=None):
    """Returns a PEP 440-compliant version number from VERSION.

    The following examples show a progression from development through
    pre-release to release and the resultant versions generated:

    >>> get_version((2, 7, 1, 'alpha', 0))
    '2.7.1.dev20150530132219'
    >>> get_version((2, 7, 1, 'alpha', 1))
    '2.7.1a1'
    >>> get_version((2, 7, 1, 'beta', 1))
    '2.7.1b1'
    >>> get_version((2, 7, 1, 'rc', 2))
    '2.7.1rc2'
    >>> get_version((2, 7, 1, 'final', 0))
    '2.7.1'
    """
    version = get_complete_version(version)

    # Now build the two parts of the version number:
    # main = X.Y[.Z]
    # sub = .devN - for pre-alpha releases
    #     | {a|b|rc}N - for alpha, beta and rc releases

    main = get_main_version(version)
    candidate_pos = _get_candidate_pos(version)
    candidate = version[candidate_pos]
    candidate_extra = version[candidate_pos+1]

    sub = ''
    if _is_development_candidate(version):
        git_changeset = get_git_changeset()
        if git_changeset:
            sub = '.dev%s' % git_changeset
        else:
            sub = '.dev0'

    elif candidate != 'final':
        mapping = {'alpha': 'a', 'beta': 'b', 'rc': 'rc'}
        sub = mapping[candidate] + str(candidate_extra)

    return str(main + sub)


def _is_development_candidate(version):
    """Is this a pre-alpha release

    >>> _is_development_candidate((2, 1, 0, 'alpha', 0))
    True
    >>> _is_development_candidate((2, 1, 0, 'beta', 1))
    False
    """
    candidate_pos = _get_candidate_pos(version)
    candidate = version[candidate_pos]
    candidate_extra = version[candidate_pos+1]
    return candidate == 'alpha' and candidate_extra == 0


def _get_candidate_pos(version):
    """Returns the position of the candidate marker.

    >>> _get_candidate_pos((1, 2, 0, 'alpha', 0))
    3
    """
    return [i for i, part in enumerate(version)
            if part in CANDIDATE_MARKERS][0]


def _get_candidate(version):
    """Returns the candidate. One of alpha, beta, rc or final.

    >>> _get_candidate((0, 1, 2, 'rc', 1))
    'rc'
    """
    return version[_get_candidate_pos(version)]


def _get_version_string(parts):
    """Returns an X.Y.Z version from the list of version parts.

    >>> _get_version_string((1, 1, 0))
    '1.1.0'
    >>> _get_version_string((1, 1, 0, 1))
    '1.1.0.1'
    """
    return '.'.join(str(x) for x in parts)


def get_main_version(version=None):
    """Returns main version (X.Y[.Z]) from VERSION.

    >>> get_main_version((1, 2, 3, 'alpha', 1))
    '1.2.3'
    """
    version = get_complete_version(version)
    candidate_pos = _get_candidate_pos(version)
    return _get_version_string(version[:candidate_pos])


def get_major_minor_version(version=None):
    """Returns X.Y from VERSION.

    >>> get_major_minor_version((1, 2, 3, 'final', 0))
    '1.2'
    """
    version = get_complete_version(version)
    return _get_version_string(version[:2])


def get_complete_version(version=None):
    """Returns a tuple of the Pootle version. Or the supplied ``version``

    >>> get_complete_version((1, 2, 3, 'alpha', 0))
    (1, 2, 3, 'alpha', 0)
    """
    if version is not None:
        return version

    return VERSION


def get_docs_version(version=None, positions=2):
    """Return the version used in documentation.

    >>> get_docs_version((1, 2, 1, 'alpha', 0))
    'dev'
    >>> get_docs_version((1, 2, 1, 'rc', 2))
    '1.2'
    """
    version = get_complete_version(version)
    candidate_pos = _get_candidate_pos(version)
    if positions > candidate_pos:
        positions = candidate_pos
    if _is_development_candidate(version):
        return 'dev'
    return _get_version_string(version[:positions])


def get_rtd_version(version=None):
    """Return the docs version string reported in the RTD site."""
    version_str = get_docs_version(version=version, positions=2)
    return (
        'latest'
        if version_str == 'dev'
        else 'stable-%s.x' % (version_str, )
    )


def _shell_command(command):
    """Return the first result of a shell ``command``"""
    repo_dir = os.path.dirname(os.path.abspath(__file__))

    try:
        command_subprocess = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=repo_dir,
            universal_newlines=True
        )
    except OSError:
        return None

    return command_subprocess.communicate()[0]


@lru_cache()
def get_git_changeset():
    """Returns a numeric identifier of the latest git changeset.

    The result is the UTC timestamp of the changeset in YYYYMMDDHHMMSS format.
    This value isn't guaranteed to be unique, but collisions are very unlikely,
    so it's sufficient for generating the development version numbers.

    >>> get_git_changeset()
    '20150530132219'
    """
    timestamp = _shell_command(
        ['/usr/bin/git', 'log', '--pretty=format:%ct', '--quiet', '-1', 'HEAD']
    )
    try:
        timestamp = datetime.datetime.utcfromtimestamp(int(timestamp))
    except ValueError:
        return None
    return timestamp.strftime('%Y%m%d%H%M%S')


@lru_cache()
def get_git_branch():
    """Returns the current git branch.

    >>> get_git_branch()
    'feature/proper_version'
    """
    branch = _shell_command(['/usr/bin/git', 'symbolic-ref', '-q',
                             'HEAD'])
    if not branch:
        return None
    return "/".join(branch.strip().split("/")[2:])


@lru_cache()
def get_git_hash():
    """Returns the current git commit hash or None.

    >>> get_git_hash()
    'ad768e8'
    """
    git_hash = _shell_command(
        ['/usr/bin/git', 'rev-parse', '--verify', '--short', 'HEAD']
    )
    if git_hash:
        return git_hash.strip()
    return None


if __name__ == "__main__":
    from sys import argv
    if len(argv) == 2:
        if argv[1] == "main":
            print(get_main_version())
        elif argv[1] == "major_minor":
            print(get_major_minor_version())
        elif argv[1] == "docs":
            print(get_docs_version())
    else:
        print(get_version())


def is_prerelease(version=None):
    """Is this a final release or not"""

    return _get_candidate(get_complete_version(version)) != 'final'
