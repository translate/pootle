#!/usr/bin/env python
"""

Dynamic loading of hooks for update and commit.

"""


import logging


def hook(project, hooktype, path, *args, **kwargs):
    """
    project should be the projectcode of any project.
    hooktype should be "initialize", "precommit", "postcommit",
    "pretemplateupdate", "preupdate", or "postupdate".
    path should be the absolute path of the file (project dir for initialize).

    Other arguments depend on the hooktype:
        initialize should have "languagecode" as an additional argument.
        precommit should have "author" and "message" as additional arguments.
        postcommit should have "success" as an additional argument.
        pretemplateupdate, preupdate, postupdate have no additional arguments.

    Return value depends on the hooktype:
        precommit returns an array of strings indicating what files to commit.
        preupdate returns the pathname of the file to update
        initialize, postcommit, and postupdate return is not used.
        pretemplateupdate returns a boolean indicating if the file should be
                          updated from template.

    """
    logger = logging.getLogger('pootle.scripts.hooks')
    try:
        activehook = __import__(project, globals(), locals(), [])
        if (hasattr(activehook, hooktype) and
                callable(getattr(activehook, hooktype))):
            logger.debug("Executing hook %s for project %s on file %s",
                         hooktype, project, path)
            return getattr(activehook, hooktype)(path, *args, **kwargs)
        else:
            logger.debug("Imported %s, but it is not a suitable %s hook",
                         activehook.__file__, hooktype)
            raise ImportError("Imported %s, but it is not a suitable %s hook" %
                              (activehook.__file__, hooktype))
    except ImportError as e:
        raise ImportError(e)
    except Exception:
        logger.exception("Exception in project (%s) hook (%s) for file (%s)",
                         project, hooktype, path)
