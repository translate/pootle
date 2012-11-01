#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob


WORKING_DIR = os.path.abspath(os.path.dirname(__file__))


def working_path(filename):
    """Return an absolute path for :parm:`filename` by joining it to
    ``WORKING_DIR``."""
    return os.path.join(WORKING_DIR, filename)


conf_files_path = os.path.join(WORKING_DIR, 'settings', '*.conf')
conf_files = glob.glob(conf_files_path)
conf_files.sort()

for f in conf_files:
    execfile(os.path.abspath(f))
