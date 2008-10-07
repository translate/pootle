#!/usr/bin/python
#Copyright (c) 2006 - 2007 by The WordForge Foundation
#                       www.wordforge.org
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# See the LICENSE file for more details. 
#
# Developed by:
#       Hok Kakada (hokkakada@khmeros.info)
#       Keo Sophon (keosophon@khmeros.info)
#       San Titvirak (titvirak@khmeros.info)
#       Seth Chanratha (sethchanratha@khmeros.info)
# 
# This module is working on the main windows of Editor

from optparse import OptionParser
from pootling.modules import MainEditor
from PyQt4 import QtCore, QtGui
import sys, os
import __version__

if (sys.argv[0].endswith('py')):
    py = 'python '
else:
    py = ''
usage = py + """%prog [OPTION] [filename]\n
if the filename is given, the editor will open the file."""
strPro = "%prog Version" + ' '  + __version__.ver
strVersion = strPro + ' \n\
Copyright (C) 2006-2007 The WordForge Foundation. www.wordforge.org\
This is free software. You may redistribute copies of it under the terms of\
the GNU General Public License <http://www.gnu.org/licenses/gpl.html>.\
There is NO WARRANTY, to the extent permitted by law.\
Written by Hok Kakada, Keo Sophon, San Titvirak, Seth Chanratha.'

parser = OptionParser(usage = usage, version = strVersion)

                  
(options, args) = parser.parse_args()
    
argc = len(args)
if (len(sys.argv) == 1):
    MainEditor.main()
else:
    path = QtCore.QDir.currentPath()
    inputFileName = os.path.abspath(args[0])
    MainEditor.main(inputFileName)
