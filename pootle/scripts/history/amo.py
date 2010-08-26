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
import StringIO

import logging
from django.conf import settings

from pootle.scripts.convert import monopo2po, po2monopo
from translate.convert import html2po, po2html

import re
try:
    import tidy
except:
    pass

def _getfiles(file):
    mainfile = os.path.join(os.path.split(file)[0], "messages.po")
    combinedfile = os.path.join(os.path.split(file)[0], "messages-combined.po")
    sourcefile = os.path.join(os.path.split(os.path.split(os.path.split(file)[0])[0])[0], "en_US", "LC_MESSAGES", "messages.po")
    return (combinedfile, mainfile, sourcefile)

def initialize(projectdir, languagecode):
    """The first parameter is the path to the project directory, including
    locale.  It's up to this script to know any internal structure of the
    directory"""

    logger = logging.getLogger('scripts.amo')
    logger.info("Initializing language %s of project %s" % (languagecode, os.path.basename(projectdir)))

    # extract project root from projectdir
    projectroot = os.path.join(settings.PODIRECTORY, os.path.split(projectdir)[0])

    # Find the files we're working with
    mainfile     = os.path.join(projectroot, languagecode, 'LC_MESSAGES', 'messages.po')
    combinedfile = os.path.join(projectroot, languagecode, 'LC_MESSAGES', 'messages-combined.po')
    sourcefile   = os.path.join(projectroot, 'en_US', 'LC_MESSAGES', 'messages.po')

    # Build our combined file
    monopo2po.convertpo(open(sourcefile, "r"), open(combinedfile, "w"), open(mainfile, "r"))

    # build .po files from the .thtml files in /pages/
    _init_pages(projectroot, languagecode)

def _init_pages(projectroot, languagecode):
    """Initialize localizable pages
    Does not do any merging. Reads in the en-US templates and makes .po files from it."""
    logger = logging.getLogger('scripts.amo')

    # we need TidyLib to import pages
    if not tidy:
        logger.debug("Cannot import pages without utidylib (http://utidylib.berlios.de/).")
        return

    enus_dir = os.path.join(projectroot, 'en_US', 'pages')
    this_dir = os.path.join(projectroot, languagecode, 'pages')

    # find all pages
    pages = os.listdir(enus_dir)
    thtml = re.compile("\.thtml$", re.IGNORECASE)
    pages = [f for f in pages if thtml.search(f)]

    for page in pages:
        # grab English template
        logger.debug('importing page %s', page)
        template = _tidy_page(os.path.join(enus_dir, page))

        converter = html2po.html2po()
        output = open(os.path.join(this_dir, page[:-6])+'.po', 'w')
        print >> output, converter.convertfile(template, page, False)

        template.close()
        output.close()

def _tidy_page(path):
    """Read a page, run it through tidy, and create a temporary output file.
    returns a temporary file object containing the results"""

    if not os.path.exists(path):
        raise IOError('file %s not found!' % path)

    # set up some tidy options
    tidy_options = {
        'char-encoding': 'utf8',
        'enclose-text': 'yes',    # wrap loose text nodes in <p>
        'show-body-only': 'auto', # do not add <html> and <body> unless present in input
        'indent': 'no',           # don't prettily indent output to make parsing easier
        'tidy-mark': 'no',        # no creator meta-tag
        'force-output': 'yes',    # some output is better than none, I hope
        }

    # unicode files make utidylib cry :( so we need to be creative
    # http://developer.berlios.de/bugs/?func=detailbug&bug_id=14186&group_id=1810
    # http://muffinresearch.co.uk/archives/2008/07/29/working-around-utidylibs-unicode-handling/
    f = open(path, 'r')
    content = unicode(f.read(), 'utf-8').encode('utf8')
    f.close()
    try:
        parsed = tidy.parseString(content, **tidy_options)
    except tidy.error.OptionArgError:
        # show-body-only is new-ish, so emulate it
        del tidy_options['show-body-only']
        try:
            parsed = tidy.parseString(content, **tidy_options)
        except Exception, e:
            print e
        bodytag = re.compile("<body>(.*)</body>", re.IGNORECASE | re.DOTALL)
        if not bodytag.search(content):
            if path.find('validation') != -1:
                print parsed
            parsed = bodytag.search(str(parsed)).group(1)

    result = StringIO.StringIO(parsed)
    result.name = os.path.basename(path)
    return result


def precommit(committedfile, author, message):
    if os.path.basename(committedfile) == "messages-combined.po":
        logger = logging.getLogger('scripts.amo')

        # Get the files we'll be using
        (combinedfile, mainfile, sourcefile) = _getfiles(committedfile)

        # Update messages.po
        logger.debug("Converting po %s to %s" % (combinedfile, mainfile))
        po2monopo.convertpo(open(combinedfile, "r"), open(mainfile, "w"))

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
        monopo2po.convertpo(open(sourcefile, "r"), open(combinedfile, "w"), open(mainfile, "r"))

def preupdate(updatedfile):
    if os.path.basename(updatedfile) == "messages-combined.po":
        logger = logging.getLogger('scripts.amo')

        # Get the files we'll be using
        (combinedfile, mainfile, sourcefile) = _getfiles(updatedfile)

        # We want to update messages.po
        logger.debug("Updating %s", mainfile)
        return mainfile
    return ""

def postupdate(updatedfile):
    logger = logging.getLogger('scripts.amo')

    # Get the files we'll be using
    (combinedfile, mainfile, sourcefile) = _getfiles(updatedfile)

    # Create the new messages-combined.po file
    logger.debug("Converting amo %s to %s with template %s" % (sourcefile, combinedfile, mainfile))
    monopo2po.convertpo(open(sourcefile, "r"), open(combinedfile, "w"), open(mainfile, "r"))
