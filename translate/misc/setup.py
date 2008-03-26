#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup, Extension
import os

class csvExtension(Extension):
  def __init__(self, source_dir):
    Extension.__init__(self, '_csv',
                    sources = [os.path.join(source_dir, '_csv.c')])

csvModule = csvExtension('.')

if __name__ == "__main__":
  setup(name="_csv",version="2.3",description="csv module",py_modules=['csv'],ext_modules=[csvModule])

