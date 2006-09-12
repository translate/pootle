#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2005, 2006 Zuza Software Foundation
# 
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""processes conflicts from msgmerge and turns them into Pootle suggestions"""

from Pootle import pootlefile
from Pootle import projects
import os

conflictmarker = "#-#-#-#-#"

def processfile(filename):
  dummyproject = projects.DummyProject(os.path.dirname(filename), None)
  pofile = pootlefile.pootlefile(dummyproject, os.path.basename(filename))
  pofile.readpofile()
  conflictitems = []
  for item, poentry in enumerate(pofile.transelements):
    msgstrs = poentry.unquotedmsgstr
    for msgstr in msgstrs:
      if conflictmarker in msgstr:
        conflictitems.append((item, msgstrs))
        break
  for item, msgstrs in conflictitems:
    replacemsgstrs = []
    for msgstr in msgstrs:
      if conflictmarker not in msgstr:
        replacemsgstrs.append(msgstr)
        continue
      lines = msgstr.split("\n")
      parts = []
      marker, part = "", ""
      for line in lines:
        if line.startswith(conflictmarker) and line.endswith(conflictmarker):
          if marker or part:
            parts.append((marker, part))
          marker = line[len(conflictmarker):-len(conflictmarker)]
          part = ""
        else:
          part += line
      if marker or part:
        parts.append((marker, part))
      for marker, part in parts:
        pofile.addsuggestion(item, part, marker.strip())
      replacemsgstrs.append("")
    pofile.setmsgstr(item, replacemsgstrs, None, None)

def processdir(dirname):
  for filename in os.listdir(dirname):
    pathname = os.path.join(dirname, filename)
    if os.path.isdir(pathname):
      processdir(pathname)
    elif filename.endswith(os.extsep + "po"):
      processfile(pathname)

if __name__ == "__main__":
  import sys
  for filename in sys.argv[1:]:
    if os.path.isdir(filename):
      processdir(filename)
    elif os.path.isfile(filename):
      processfile(filename)
    else:
      print >>sys.stderr, "cannot process", filename


