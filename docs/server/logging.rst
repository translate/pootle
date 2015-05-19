Logging
=======

Pootle's default logging has configurations for all important aspects of the
server that we want to log.  Pootle also logs to the 'action' logger that will
log every user, system and command action executed on the server.

Action logger
-------------

The action logger logs each activity related to translation, units changes,
store changes, command execution and other activities.

The log message is as follows:

``[2015-05-04T15:06:39]   system  X   ./manage.py update_tmserver``

That is:

``[date] user type message``

Action types
~~~~~~~~~~~~

Current action types are as follows:

.. See: https://github.com/translate/pootle/blob/master/pootle/core/log.py#L14-L32
   for any that might be missing.

+----------+--------------+-------------------------------------------------+
|  Action  | Group        | Description                                     |
+==========+==============+=================================================+
|  A       | Translation  | Translation submission added a translation      |
+----------+--------------+-------------------------------------------------+
|  C       | Translation  | An existing translation was changed             |
+----------+--------------+-------------------------------------------------+
|  D       | Translation  | An existing translation was deleted             |
+----------+--------------+-------------------------------------------------+
|  UA      | Unit         | A new unit was added                            |
+----------+--------------+-------------------------------------------------+
|  UO      | Unit         | An existing unit was made obsolete              |
+----------+--------------+-------------------------------------------------+
|  UR      | Unit         | An obsolete unit was resurected i.e. reinstated |
+----------+--------------+-------------------------------------------------+
|  UD      | Unit         | An existing unit was deleted                    |
+----------+--------------+-------------------------------------------------+
|  SA      | Store        | A new store was added                           |
+----------+--------------+-------------------------------------------------+
|  SO      | Store        | An existing store was made obsolete             |
+----------+--------------+-------------------------------------------------+
|  SR      | Store        | An obsolete store was reinstated                |
+----------+--------------+-------------------------------------------------+
|  SD      | Store        | An existing store was deleted                   |
+----------+--------------+-------------------------------------------------+
|  X       | Command      | A ``./manage.py`` command was executed          |
+----------+--------------+-------------------------------------------------+
|  QM      | Quality      | A quality check was muted (marked as a false    |
|          | check        | positive)                                       |
+----------+--------------+-------------------------------------------------+
|  QU      | Quality      | A quality check was unmuted (reenabled after    |
|          | check        | having been muted)                              |
+----------+--------------+-------------------------------------------------+
|  SC      | Score        | A users score has changed because of an action  |
+----------+--------------+-------------------------------------------------+
|  PTA     | Paid Task    | A paid task has been added                      |
+----------+--------------+-------------------------------------------------+
|  PTD     | Paid Task    | A paid task has been deleted                    |
+----------+--------------+-------------------------------------------------+

