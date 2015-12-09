pootle-invoices
===============

Generate invoices out of Pootle users' activity and send them via e-mail.


Setup
-----

Installation can be done via PyPI using pip:

.. code-block:: shell

  $ pip install pootle-invoices


Configure it:

.. code-block:: python

  INSTALLED_APPS += [
    'pootle_invoices',
  ]

  POOTLE_INVOICES_COMPANY = "ACME"
  POOTLE_INVOICES_DEPARTMENT = "Awesome department"

  POOTLE_INVOICES_DIRECTORY = '/home/l10n/pootle/invoices'

  POOTLE_INVOICES_RECIPIENTS = {
    # List of users for whom invoices will be generated and send to
  }


Invoices can be generated in PDF format as well by using `PhantomJS
<http://phantomjs.org/>`_. To use this feature, adjust PhantomJS's binary
location as needed:

.. code-block:: python

  POOTLE_INVOICES_PHANTOMJS_BIN = '/usr/local/bin/phantomjs'


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


XXXX
----

Set user rates/currency (from reports)
USD is hard-coded


Specifying invoice recipients
-----------------------------

The list of users for whom invoices will be generated and send to is specified
in the ``POOTLE_INVOICES_RECIPIENTS`` setting.

The setting holds a dictionary where the keys are actual usernames of the
running Pootle instance and the values are dictionaries of key-value pairs which
will be used to construct individual invoices.

.. code-block:: python


  POOTLE_INVOICES_RECIPIENTS = {
      'johndoe': {
          # Full name as displayed in the invoice
          'name': 'John Doe',
          # Recipient's email address
          'email': 'johndoe@example.com',
          # (REQUIRED)
          # Accounting department's email
          'accounting-email': 'acc@example.com',
          'accounting-email-cc': 'other.accountant@example.com',
          'invoice_prefix': '-',
          'language': 'eu',
          'minimal_payment': 50, # USD
          'extra_add': 30, # +30 USD wire transfer reimbursement
          'paid_by': 'Evernote Corp.',
          'wire_info': u"""
              Name on Account: John Doe
              Bank: TEST BANK
              SWIFT: SWIFT number
              Agency: Agency number
              Current Account: Acc. number
              CPF: C.P.F. number
              """,
      },
  }


LICENSE
-------

pootle-invoices is released under the General Public License, version 3 or
later. See the file LICENSE for details.
