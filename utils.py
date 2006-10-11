# from django.utils.translation import gettext_lazy as _
from gettext import gettext as _
import sre

import traceback
import sys

def deprecated(func):
    def __depr__(*args, **kwargs):
        print 'This function is deprecated', func
        return func(*args, **kwargs)
    return __depr__

def shortdescription(descr):
    """Returns a short description by removing markup and only including up
    to the first br-tag"""
    stopsign = descr.find("<br")
    if stopsign >= 0:
        descr = descr[:stopsign]
    return sre.sub("<[^>]*>", "", descr).strip()

# ex pagelayout.PootleNavPage.makelink
def makelink(argdict, link, **newargs):
    """constructs a link that keeps sticky arguments e.g. showchecks"""
    combinedargs = argdict.copy()
    combinedargs.update(newargs)
    if '?' in link:
        if not (link.endswith("&") or link.endswith("?")):
            link += "&"
    else:
        link += '?'
    # TODO: check escaping
    link += "&".join(["%s=%s" % (arg, value) for arg, value in combinedargs.iteritems() if arg != "allowmultikey"])
    return link

# ex pagelayout.PootleNavPage.getbrowseurl
def getbrowseurl(argdict, basename, **newargs):
    """gets the link to browse the item"""
    if not basename or basename.endswith("/"):
        return makelink(argdict, basename or "index.html", **newargs)
    else:
        return makelink(argdict, basename, translate=1, view=1, **newargs)

def makenavbarpath_dict(project=None, session=None, currentfolder=None, language=None, argdict={}):
    """create the navbar location line"""
    rootlink = ""
    paramstring = ""
    if argdict:
      paramstring = "?" + "&".join(["%s=%s" % (arg, value) for arg, value in argdict.iteritems() if arg.startswith("show") or arg == "editing"])

    links = {"admin": None, "project": [], "language": [], "goal": [], "pathlinks": []}
    if currentfolder:
      pathlinks = []
      dirs = currentfolder.split("/")
      depth = len(dirs)
      if currentfolder.endswith(".po"):
        depth = depth - 1
      rootlink = "/".join([".."] * depth)
      if rootlink:
        rootlink += "/"
      for backlinkdir in dirs:
        if backlinkdir.endswith(".po"):
          backlinks = "../" * depth + backlinkdir
        else:
          backlinks = "../" * depth + backlinkdir + "/"
        depth = depth - 1
        pathlinks.append({"href": getbrowseurl(argdict, backlinks), "text": backlinkdir, "sep": " / "})
      if pathlinks:
        pathlinks[-1]["sep"] = ""
      links["pathlinks"] = pathlinks
    if argdict and "goal" in argdict:
      # goallink = {"href": getbrowseurl(argdict, "", goal=goal), "text": goal}
      links["goal"] = {"href": getbrowseurl(argdict, ""), "text": _("All goals")}
    if project:
      if isinstance(project, tuple):
        projectcode, projectname = project
        links["project"] = {"href": "/projects/%s/%s" % (projectcode, paramstring), "text": projectname}
      else:
        links["language"] = {"href": rootlink + "../index.html", "text": project.languagename}
        # don't getbrowseurl on the project link, so sticky options won't apply here
        links["project"] = {"href": (rootlink or "index.html") + paramstring, "text": project.projectname}
        if session:
          if "admin" in project.getrights(session) or session.issiteadmin():
            links["admin"] = {"href": rootlink + "admin.html", "text": _("Admin")}
    elif language:
      languagecode, languagename = language
      links["language"] = {"href": "/%s/" % languagecode, "text": languagename}
    return links

