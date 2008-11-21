#!/usr/bin/python
import sys
import os
import os.path
import subprocess

def hook(project, hooktype, file, *args, **kwargs):
  """
  project should be the projectcode of any project.
  hooktype should be precommit, postcommit, preupdate or postupdate.
  file should be the absolute path of the file.

  Other arguments depend on the hooktype:
    precommit should have "author" and "message" as arguments.
    postcommit should have "success" as arguments.
    preupdate and postupdate have no additional arguments.

  Return value depends on the hooktype:
    precommit returns an array of strings indicating what files to commit .
    preupdate returns an array of strings indicating what files to update.
    postcommit and postupdate return unit.

  """
  try:
    activehook = __import__(project, globals(), locals(), [])
    if hasattr(activehook, hooktype) and callable(getattr(activehook, hooktype)):
        return getattr(activehook, hooktype)(file, *args, **kwargs)
    else:
        return []
  except ImportError, e:
    raise ImportError(e)
  except Exception, e:
    print "Exception in project (%s) hook (%s) for file (%s): %s" % (project, hooktype, file, e)
