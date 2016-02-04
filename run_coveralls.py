#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

# This file was cribbed from https://github.com/brechtm/citeproc-py

import os
from distutils.sysconfig import get_python_lib
from subprocess import call


if __name__ == '__main__':
    # chdir to the site-packages directory so the report lists relative paths
    orig_dir = os.getcwd()
    dot_coverage_path = os.path.join(orig_dir, '.coverage')
    os.chdir(get_python_lib())
    try:
        os.remove('.coverage')
    except OSError:
        pass
    os.symlink(dot_coverage_path, '.coverage')

    # create a report from the coverage data
    if 'TRAVIS' in os.environ:
        rc = call('coveralls')
        raise SystemExit(0)
    else:
        rc = call(['coverage', 'report'])
        raise SystemExit(rc)
