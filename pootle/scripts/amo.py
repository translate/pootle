#!/usr/bin/python

# Verbatim script for managing the addons.mozilla.org project.  More information at
# https://wiki.mozilla.org/Verbatim
#
# Authors:
# Wil Clouser <clouserw@mozilla.com>
# Dan Schafer <dschafer@andrew.cmu.edu>
# Frederic Wenzel <fwenzel@mozilla.com>

import sys
import os
import os.path
import subprocess
import logging
from Pootle.scripts.convert import monopo2po, po2monopo

def _getfiles(file):
  mainfile = os.path.join(os.path.split(file)[0], "messages.po")
  combinedfile = os.path.join(os.path.split(file)[0], "messages-combined.po")
  sourcefile = os.path.join(os.path.split(os.path.split(os.path.split(file)[0])[0])[0], "en_US", "LC_MESSAGES", "messages.po")
  return (combinedfile, mainfile, sourcefile)

def initialize(projectdir, languagecode):
  """The first paramater is the path to the project directory.  It's up to this
  script to know any internal structure of the directory"""

  logger = logging.getLogger('scripts.amo')
  logger.info("Initializing language %s of project %s" % (languagecode, os.path.basename(projectdir)))

  # Find the files we're working with
  mainfile     = os.path.join(projectdir, languagecode, 'LC_MESSAGES', 'messages.po')
  combinedfile = os.path.join(projectdir, languagecode, 'LC_MESSAGES', 'messages-combined.po')
  sourcefile   = os.path.join(projectdir, 'en_US', 'LC_MESSAGES', 'messages.po')

  # Build our combined file
  monopo2po.convertpo(open(sourcefile,"r"), open(combinedfile,"w"), open(mainfile,"r"))

  # TODO
  # Eventually we'll need to build .po files from the .thtml files in /pages/ but
  # running html2po on localized files doesn't make sense


def precommit(committedfile, author, message):
  if os.path.basename(committedfile) == "messages-combined.po":
    logger = logging.getLogger('scripts.amo')

    # Get the files we'll be using
    (combinedfile, mainfile, sourcefile) = _getfiles(committedfile)
    
    # Update messages.po 
    logger.debug("Converting po %s to %s" % (combinedfile, mainfile))
    po2monopo.convertpo(open(combinedfile,"r"), open(mainfile,"w"))

    # We want to commit messages.po
    return [mainfile]
  return []

def postcommit(committedfile, success):
  if os.path.basename(committedfile) == "messages.po":
    logger = logging.getLogger('scripts.amo')
    
    # Get the files we'll be using
    (combinedfile, mainfile, sourcefile) = _getfiles(committedfile)

    # Recreate messages-combined.po 
    logger.debug("Converting amo %s to %s with template %s" % (sourcefile, combinedfile, mainfile))
    monopo2po.convertpo(open(sourcefile,"r"), open(combinedfile,"w"), open(mainfile,"r"))

def preupdate(updatedfile):
  if os.path.basename(updatedfile) == "messages-combined.po":
    logger = logging.getLogger('scripts.amo')

    # Get the files we'll be using
    (combinedfile, mainfile, sourcefile) = _getfiles(updatedfile)
    
    # We want to update messages.po
    logger.debug("Updating %s" % mainfile)
    return mainfile
  return ""

def postupdate(updatedfile):
  logger = logging.getLogger('scripts.amo')

  # Get the files we'll be using
  (combinedfile, mainfile, sourcefile) = _getfiles(updatedfile)

  # Create the new messages-combined.po file
  logger.debug("Converting amo %s to %s with template %s" % (sourcefile, combinedfile, mainfile))
  monopo2po.convertpo(open(sourcefile,"r"), open(combinedfile,"w"), open(mainfile,"r"))
