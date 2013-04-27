#!/usr/bin/env python

# Verbatim script for managing the SUMO (support.mozilla.com) project.  More information at
# https://wiki.mozilla.org/Verbatim
#
# [Note that this is a historical example only, as SUMO no longer uses tiki.]
#
# Author: Wil Clouser <clouserw@mozilla.com>

import os
import logging

from django.conf import settings

from translate.convert import tiki2po, po2tiki


def initialize(projectdir, languagecode):
    """The first parameter is the path to the project directory.  It's up to this
    script to know any internal structure of the directory"""

    # Temporary code - projectdirs come from pootle with sumo/ab_CD form; we need just the former part
    # extract project root from projectdir
    projectroot = os.path.join(settings.PODIRECTORY, os.path.split(projectdir)[0])

    # Temporary code.  Language codes come from pootle with underscores right now; they need to be dashes.
    languagecode = languagecode.replace("_", "-")

    # Find the files we're working with
    tikifile = os.path.join(projectroot, languagecode, 'language.php')
    pofile   = os.path.join(projectroot, languagecode, 'language.po')

    # Build our combined file
    logging.info(u"Initializing %s to %s", tikifile, pofile)
    tiki2po.converttiki(open(tikifile, "r"), open(pofile, "w"))

def precommit(committedfile, author, message):
    if os.path.basename(committedfile) == "language.po":

        # Get the files we'll be using
        tikifile = os.path.join(os.path.dirname(committedfile), 'language.php')

        # Update tikifile with new strings
        logging.info(u"Converting po to tiki: %s > %s", committedfile, tikifile)
        po2tiki.convertpo(open(committedfile, "r"), open(tikifile, "w"))

        # We want to commit language.php
        return [tikifile]
    return []

def postcommit(committedfile, success):
    if os.path.basename(committedfile) == "language.po":

        # Get the files we'll be using
        tikifile = os.path.join(os.path.dirname(committedfile), 'language.php')

        # Recreate .po with any new strings in tikifile
        logging.info(u"Converting tiki to po: %s > %s", tikifile, committedfile)
        tiki2po.converttiki(open(tikifile, "r"), open(committedfile, "w"))

def preupdate(updatedfile):
    if os.path.basename(updatedfile) == "language.po":

        # Get the files we'll be using
        tikifile = os.path.join(os.path.dirname(updatedfile), 'language.php')

        # We want to update language.php
        logging.info(u"Updating %s", tikifile)
        return tikifile
    return ""

def postupdate(updatedfile):
    if os.path.basename(updatedfile) == "language.po":

        # Get the files we'll be using
        tikifile = os.path.join(os.path.dirname(updatedfile), 'language.php')

        # Recreate .po with any new strings in tikifile
        logging.info(u"Converting tiki to po: %s > %s", tikifile, updatedfile)
        tiki2po.converttiki(open(tikifile, "r"), open(updatedfile, "w"))
