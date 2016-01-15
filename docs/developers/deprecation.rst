.. _deprecation:

Deprecation
===========

From time to time features, commands, configurations will be deprecated.  We
deprecate and manage backward compatibility within the following guidelines:

1. Our priority is the movement of Pootle development forward.  Thus:

   1. We don't want to have to maintain backward compatibility for too long as
      it hampers forward mobility.
   2. We won't maintain backward compatibility if that prevents or impacts the
      needs of the new feature, refactoring, etc.
   3. We won't maintain backward compatibility if the cost of that far
      outweights the effort of reconfiguring Pootle.

2. We don't want there to be major disruptions that we can avoid with point
   release.  That is it shouldn't be painful as we shift features.
3. Nothing is forever.  We won't maintain deprecation or backward compatibility
   for long.


The "rules" of deprecation
--------------------------

So some rough "rules".  These apply to features, management commands and
settings.

1. If it's **not released**.  Drop it and tell others on `Pootle development
   channel <https://gitter.im/translate/dev>`_.  If it has settings add them to
   the settings deprecation infrastructure to force removal if required.
2. If it is **obsolete or replaced** with an equivalent then drop with no
   fanfare and add settings to the deprecation infrastructure so that an admin
   will remove settings from their settings files.  Add to release notes if
   needed.
3. If it has been **renamed**.  Put that in the release notes and allow
   fallback for one version.  Use deprecation infrastructure for settings to
   allow old settings to continue to work until the N+1 release.  After that
   its a hard failure.  For commands simply rename.
4. If things **changed**.  For settings put that in release notes and do a hard
   failure to ensure that admins will reconfigure.  For commands, just put
   those notes in the release notes and in the command features.
5. If **removed**. Put in release notes.  For settings choose either hard or
   soft failure depending on whether something needs to be done by the admin.
   Put in release notes together with a guide on how to work around the missing
   feature if its possible. for commands simply make sure they are highlighted
   as removed in the release notes.


Implementing a deprecated setting
---------------------------------

1. Add the newly deprecated setting to :file:`pootle/core/utils/deprecation.py`
   ``DEPRECATIONS``.
2. Move the deprecated setting to the deprecated section in the :doc:`settings
   </server/settings>` document. With the needed ``.. deprecated:: N.M``
   marker.
3. Add to the release notes.
