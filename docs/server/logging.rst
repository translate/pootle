Logging
=======

Pootle's default logging has configurations for all important aspects of the
server that we want to log.  Pootle also logs to the 'action' logger that will
log every user, system and command action executed on the server.

Log directory
-------------

You can override the default logging directory by specifying the
:setting:`POOTLE_LOG_DIRECTORY` setting.

Action logger
-------------

The action logger logs each activity related to translation, units changes,
store changes, command execution and other activities.

The generic log message is as follows (though some actions do produce slightly
different log entries)::

  [2015-05-04T15:06:39]   system  X   ./manage.py update_tmserver

That is::

  [date] user type message

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


Score Translation Actions
~~~~~~~~~~~~~~~~~~~~~~~~~

In addition the SC action type also has its own actions which track the actual
type of activity that leads to changes in translation.  These are used to track
scores for the translators.

.. These are taken from
   https://github.com/translate/pootle/blob/master/pootle/apps/pootle_statistics/models.py#L297-L325
   and should be updated as needed.

========= ==============================================================
 Action    Description
========= ==============================================================
  TA       unit translated
  TE       unit edited after someone else
  TX       unit edited after themselves
  TD       translation deleted by admin
  R        translation reviewed
  TF       translation’s fuzzy flag is set by admin
  XE       translation penalty [when translation deleted]
  XR       translation penalty [when review canceled]
  S        suggestion added
  SA       suggestion accepted (counted towards the suggestion author)
  SR       suggestion rejected (counted towards the suggestion author)
  RA       suggestion accepted (counted towards the reviewer)
  RR       suggestion rejected (counted towards the reviewer)
========= ==============================================================



Action messages
~~~~~~~~~~~~~~~

Various of the action groups have different message structures as outlined here:

*Translation*::

  date  user  action  lang    unit    path    translation
  [2015-05-19T14:11:18]   admin   C       af      2       /af/tutorial/stats-test.po      Twee
  [2015-05-19T14:12:17]   admin   A       af      3       /af/tutorial/stats-test.po      Drie
  [2015-05-19T14:13:05]   admin   D       af      1       /af/tutorial/stats-test.po

*Unit*::

  date  user    action  language    unit    file    translation
  [2015-05-06T16:25:20]	system	UA	am	4109	/am/terminology/gnome/am.po	MSDOS
  [2015-05-06T16:37:05]	system	UA	cs	12043	/cs/terminology/gnome/cs.po	přepínač

*Store*::

  date  user    action  path    store
  [2015-05-05T20:23:37]	system	SA	/templates/tutorial/tutorial.pot	1

*Command*::

  date  user  action command
  [2015-05-06T11:24:28]	system	X	./manage.py update_stores --project=vfolders
  [2015-05-05T20:22:46]	system	X	./manage.py migrate

*Quality check*::

  date  user    action  lang    unit    path    translation
  [2015-05-19T14:16:36]   admin   QM      af      855     /af/terminology/gnome-terminologie.po   lug
  [2015-05-19T14:17:44]   admin   QU      af      855     /af/terminology/gnome-terminologie.po   lug

*Score*::

  date  user    SC  score_delta  score_action    #unit  NS=wordcount    S=similarity   total
  [2015-05-19T14:19:11]   admin   SC      1.0     TA      #1      NS=1    S=0.0   (total: 2.28571428571)

*Paid Task*::

  date  user    action  Task: [id, user, date, type, amount, comment]
  [2015-05-19T14:35:34]   admin   PTA     Task: [id=1, user=admin, month=2015-05, type=Translation, amount=1000.0, comment=Translate UI]


Sync and Update messages
~~~~~~~~~~~~~~~~~~~~~~~~

The :djadmin:`sync_stores` and :djadmin:`update_stores` commands will produce a
number of logs to report any activity that results from those commands.

*update_stores*::

  [$date] [update] updated $number units in $store_path [revision: $revision]
  [2015-05-19T21:06:24]   [update] updated 1 units in /an/libo_ui/dictionaries/pt_PT.po [revision: 58]

*sync_stores*::

  [$date]   [sync] File saved; updated $number units in $store_path [revision: $revision]
  [2015-05-19T23:11:50]   [sync] File saved; updated 1 units in /an/libo_ui/avmedia/source/viewer.po [revision: 0]
