#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob

from install_dirs import *

conf_files_path = os.path.join(SOURCE_DIR, 'settings', '*.conf')
conf_files = glob.glob(conf_files_path)
conf_files.sort()

for f in conf_files:
    execfile(os.path.abspath(f))
