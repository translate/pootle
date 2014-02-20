import os
from django.conf import settings
from translate.convert import html2po, po2html

def initialize(projectdir, languagecode):
    print "*************** initialize: %s, %s" % (projectdir, languagecode)
    pass

def precommit(commitfile, author, message):
    print "*************** precommit %s, %s, %s" % (commitfile, author, message)
    if 'help.html' not in commitfile:
        print 'commit to %s' % commitfile
        return [commitfile]
    elif '.pot' in commitfile:
        print 'ignore file'
        return []
    elif 'de_DE' in commitfile:
        print 'ignore file'
        return []
    else:
        pofile = os.path.join(settings.PODIRECTORY, commitfile)
        htmlfile = os.path.join(settings.PODIRECTORY, os.path.dirname(commitfile), 'help.html')
        template = os.path.join(settings.VCS_DIRECTORY, commitfile.split('/')[0], 'de_DE/help.html')
        print 'Converting po to html: %s to %s' % (pofile, htmlfile)
        with open(pofile, 'r') as po:
            with open(htmlfile, 'w') as html:
                with open(template, 'r') as templ:
                    po2html.converthtml(po, html, templ)
        print 'commit to %s' % htmlfile
        return [htmlfile]

def postcommit(updatedfile, success):
    print "*************** postcommit %s, %s" % (updatedfile, success)

def preupdate(updatedfile):
    print "*************** preupdate %s" % updatedfile
    if 'help.html.pot' in updatedfile:
        htmlfile = os.path.join(updatedfile.split('/')[0], 'de_DE/help.html')
        print 'rewrite to %s' % htmlfile
        return htmlfile
    else:
        return updatedfile

def postupdate(updatedfile):
    print "*************** postupdate %s" % updatedfile
    if 'help.html.pot' in updatedfile:
        potfile = os.path.join(settings.PODIRECTORY, updatedfile)
        htmlfile = os.path.join(settings.VCS_DIRECTORY, updatedfile.split('/')[0], 'de_DE/help.html')
        print 'Converting de_DE html to pot: %s to %s' % (htmlfile, potfile)
        with open(htmlfile, 'r') as html:
            with open(potfile, 'w') as pot:
                html2po.converthtml(html, pot, None, pot=True)

def pretemplateupdate(updatedfile):
    print "*************** pretemplateupdate %s" % updatedfile
    if 'de_DE' in updatedfile and 'help.html' in updatedfile:
        return False
    return True
