.. _rq:

RQ Job Queues
=============

Pootle makes use of RQ to manage background jobs.

Currently statistics are calculated using background jobs and we expect more
components to use it in future.

The RQ queue is managed by Redis and it is setup in the `RQ_QUEUES
<https://github.com/ui/django-rq#installation>`_ and :setting:`CACHES`
settings.


Running job workers
-------------------

The queue is processed by Workers.  Any number of workers may be started and
will process jobs in the default queue.  The :djadmin:`rqworker` command is
used to start a Worker.


Monitoring the queue
--------------------

At the simplest level the Admin dashboard will tell you if the queue is active
and how many workers are available to service the queue.  It also lists the
number of pending jobs and the number of failed jobs.  This gives you a quick
way to see if anything is wrong.


Working with failed jobs
------------------------

If a job fails it needs to be investigated. In most cases a traceback will
indicate why the job failed.

The simplest way to work with queues and jobs is to use `rq-dashboard
<https://github.com/nvie/rq-dashboard>`_, though you likely don't want to
deploy that on a production server.  With this you can see the jobs in the
queue, you can check the tracebacks and you can retry failed jobs.

In the case of a production server you can make use of the following commands
to manage jobs:

.. code-block:: console

   $ redis-cli -n 2 lrange rq:queue:default 0 -1
   03135097-00f8-46eb-b084-6f34a16d9940
   a07309b3-f056-47e7-856c-c608bda2f171
   3df6a559-2e3c-4c0c-b09c-1948b4bacda2

This will display all pending job IDs in the default queue. We're using
the Redis DB number ``2``, the default RQ queue on a standard Pootle install.

.. code-block:: console

   $ redis-cli -n 2 lrange rq:queue:failed 0 -1
   60ed13df-0ce5-4b98-96f0-f8e0294ba421
   3240527f-58b9-40fe-b0c5-b8d3fcaa06b6


This will display the failed job IDs.

To investigate a failed job simply add ``rq:job:`` prefix to a job ID and
use a command such as this:

.. code-block:: console

   $ redis-cli -n 2 hgetall rq:job:60ed13df-0ce5-4b98-96f0-f8e0294ba421


This will allow you to see any traceback and investigate and solve them.

To push failed jobs back into the queue we simply run the
:djadmin:`retry_failed_jobs` management command.


Delete all failed jobs
++++++++++++++++++++++

Sometimes failed jobs no longer apply since they refer to removed items, so no
matter how many times you run them they will keep failing. Note that sometimes
those unrecoverable failed jobs are in company of other failed jobs that can be
re-run by using the :djadmin:`retry_failed_jobs` management command:

.. code-block:: console

   $ pootle retry_failed_jobs


In order to delete all the failed jobs you must first **stop the workers**.

Once the workers are stopped make sure that there are no failed jobs that you
don't want to remove. In case there is any restart the workers to re-run them
with :djadmin:`retry_failed_jobs`. Stop the workers again once those jobs are
completed. Check again that all the failed jobs are the ones you want to
remove.

In order to perform a bulk delete of all failed jobs run the following
commands:

.. code-block:: console

   $ redis-cli -n 2 LRANGE "rq:queue:failed" 0 -1 | perl -nE 'chomp; `redis-cli DEL rq:job:$_`;'


Now remove the list of failed jobs:

.. code-block:: console

   $ redis-cli -n 2 DEL "rq:queue:failed"


Do not forget to **restart the workers**.


Dirty statistics
----------------

When we count stats with :djadmin:`refresh_stats` Pootle will track a dirty
count so that it knows when the counts for that part of the tree is complete.

When debugging a situation where the counts aren't completing it is helpful to
see the dirty counts.  To retrieve these use:

.. code-block:: console

   $ redis-cli -n 2 zrank "pootle:dirty:treeitems" "/projects/terminology/"

Or to get a complete list for the server, including the scores:

.. code-block:: console

   $ redis-cli -n 2 zrange "pootle:dirty:treeitems" 0 -1 withscores

The banner that shows that stats are being calculated is displayed when
``pootle:refresh:stats`` is present.  Only remove this if you are confident
that all else is good and that the stats are fine or to be generated again.

.. code-block:: console

   $ redis-cli -n 2 del pootle:refresh:stats


Delete dirty counts
+++++++++++++++++++

Sometimes statistics are correctly calculated, but the banner telling that
stats are being refreshed doesn't dissappear. This usually happens because some
job failed to complete and thus it didn't decrease the dirty counts.

Make sure that there are no pending jobs or jobs being run since those could
have increased the dirty counts. Re-run failed jobs if any.

In order to delete all the dirty counts you must **stop the workers**.

Remove the ``lastjob`` info for all dirty items:

.. code-block:: console

   $ redis-cli -n 2 ZRANGEBYSCORE "pootle:dirty:treeitems" 1 10000 | perl -nE 'chomp; s/\/$//; s/^\///; s/\//./g; `redis-cli -n 2 DEL pootle:stats:lastjob:$_`'


Now remove the dirty items:

.. code-block:: console

   $ redis-cli -n 2 ZRANGEBYSCORE "pootle:dirty:treeitems" 1 10000 | perl -nE 'chomp; `redis-cli -n 2 ZREM pootle:dirty:treeitems $_`'


Do not forget to **restart the workers**.
