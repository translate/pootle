pootle-invoices
===============

Generate invoices out of Pootle users' activity and send them via e-mail.


Usage
-----

A new ``generate_invoices`` management command is available after installing
pootle-invoices. This can be run manually, or can be scripted to run
periodically at will.

Running ``generate_invoices`` without any arguments will generate invoices for
the current month. A specific month can be specified by passing the
``--debug-month=<YYYY-NN>`` argument.

.. code-block:: shell

  $ ./manage.py generate_invoices --month=<YYYY-MM>

Invoices will be generated in the ``$POOTLE_INVOICES_DIRECTORY/<YYYY-MM>/``
folder.

The list of users for whom invoices will be generated can be limited to a subset
of the configured users by passing the ``--user-list=<user1, user2... userN>``
argument.

Invoices will also be sent by email if the ``--send-emails`` flag is set. There
are a couple more options to control how email will be sent:

  * ``--bcc-send-to``: allows specifying BCC recipients.
  * ``--debug-send-to``: DEBUG email list (?)
