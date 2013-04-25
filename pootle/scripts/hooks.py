#!/usr/bin/env python

import logging


def hook(project, hooktype, file, *args, **kwargs):
    """
    project should be the projectcode of any project.
    hooktype should be precommit, postcommit, preupdate or postupdate.
    file should be the absolute path of the file.

    Other arguments depend on the hooktype:
        precommit should have "author" and "message" as arguments.
        postcommit should have "success" as arguments.
        pretemplateupdate, preupdate, postupdate have no additional arguments.

    Return value depends on the hooktype:
        precommit returns an array of strings indicating what files to commit.
        preupdate returns an array of strings indicating what files to update.
        postcommit and postupdate return unit.
        pretemplateupdate returns a boolean indicating if the file should be
                          updated from template.

    """
    logger = logging.getLogger('pootle.scripts.hooks')
    try:
        activehook = __import__(project, globals(), locals(), [])
        if (hasattr(activehook, hooktype) and
                callable(getattr(activehook, hooktype))):
            logger.debug("Executing hook %s for project %s on file %s",
                         hooktype, project, file)
            return getattr(activehook, hooktype)(file, *args, **kwargs)
        else:
            logger.debug("Imported %s, but it is not a suitable %s hook",
                         activehook.__file__, hooktype)
            raise ImportError("Imported %s, but it is not a suitable %s hook" %
                              (activehook.__file__, hooktype))
    except ImportError, e:
        raise ImportError(e)
    except Exception, e:
        logger.error("Exception in project (%s) hook (%s) for file (%s): %s" %
                     (project, hooktype, file, e))
