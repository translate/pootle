.. _rq:

RQ Job Queues
=============

Pootle makes use of RQ to manage background jobs.

Currently statistics are calculated using background jobs and we expect more
components to use it in future.

The RQ queue is managed by redis and it setup in the `RQ_QUEUES
<https://github.com/ui/django-rq#installation>`_ and :setting:`CACHES`
settings.


Monitoring the queue
--------------------

At the simplest level the Admin dashboard will tell you if the queue is active
and how many workers are available to service the queue.  It also lists the
number of pending jobs and the number of failed jobs.  This gives you a quick
way to see if anything is wrong.


Working with failed jobs
------------------------

If a job fails it need to be investigated. In most cases a traceback will
indicate why the job failed.

The simplest way to work with queues and jobs is to use `rq-dashboard
<https://github.com/nvie/rq-dashboard>`_, though you likely don't want to deply
that on a deployed server.  With this you can see the jobs in the queue, can
check the tacebacks and can retry failed jobs.

In the case of a deployed server you can make use of the following commands to
manage jobs::

  $ redis-cli -n 2 keys '*' | grep rq:job
  rq:job:03135097-00f8-46eb-b084-6f34a16d9940
  rq:job:a07309b3-f056-47e7-856c-c608bda2f171
  rq:job:3df6a559-2e3c-4c0c-b09c-1948b4bacda2
  rq:job:60ed13df-0ce5-4b98-96f0-f8e0294ba421
  rq:job:3240527f-58b9-40fe-b0c5-b8d3fcaa06b6

This will display the current jobs in the queue. We're using the cache number
``2``, the default RQ queue on a standard Pootle install.

To investigate a failed job simpley use a command such as this::

  $ redis-cli -n 2 hgetall rq:job:5beee45b-e491-4e78-9471-e7910b2d2514 

This will allow you to see any traceback and investigate and solve them.

To push failed jobs back into the queue we simply run the
:djadmin:`retry_failed_jobs` mmanagement command.
