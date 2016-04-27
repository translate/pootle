.. _invoices:

Invoice Generation
==================

Out of users' activity and with the help of some extra configuration, Pootle is
able to generate monthly-based invoices and optionally send them via e-mail.
This is useful when paid contractors and/or agencies are involved in the
translation process.


.. _invoices#calculation:

Calculation of Payments
-----------------------

Payments are calculated based on the :ref:`rates set for users
<invoices#configuring>` and the amount of work they have performed during the
month being processed. Rates can be set per translated word, per reviewed word
or per hour.

The amount of work is measured considering the following activities:

* The number of translated words.
* The number of reviewed words.
* The number of hours dedicated to a specific :ref:`paid task
  <invoices#calculation-paid-tasks>`.

Each type of work is multiplied by the rates set for the user, and is summed up
to get the total amount corresponding to the work performed during the month.

Note this might not be the final amount though, as it still needs to go through
potential :ref:`carry-overs and extra payments
<invoices#calculation-corrections>`.


.. _invoices#calculation-corrections:

Carry-overs and Extra Payments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A minimal amount to be paid can optionally be set on a user-specific basis via
the ``minimal_payment`` user configuration key. In such cases, when the total
amount to be paid for the current month is lower than the minimal payment amount
set for a user, the total amount will be carried over to the next month.

When running the command in a subsequent month, the carried-over amount will be
added to the totals as a correction.

Extra fixed amounts to be paid can also be added for individuals, as a way to
indicate reimbursements for transaction fees or similar. This is controlled by
the ``extra_add`` user configuration key.


.. _invoices#calculation-paid-tasks:

Paid Tasks
^^^^^^^^^^

There might be ocassions where some translation activities happened out of
Pootle (e.g. via spreadsheets or documents sent via e-mail), and the way to
track these is by manually adding paid tasks.

Such tasks can refer to the translation or review of a certain amount of words,
as well as hour-based activities. Other type of corrections can be added here,
too. These tasks allow adding a description to easily identify the type of work
being reported.

In order to manually add paid tasks, administrators can go to the *Reports*
section of the administration site, select a user from the drop-down and add
tasks below.

Alternatively this can also be done by translators themselves by going to their
statistics page and adding the tasks right below their daily activity graph.
This option is only available to them once an administrator has set payment
rates for them.


.. _invoices#calculation-subcontractors:

Subcontractors
^^^^^^^^^^^^^^

A paid contractor can act as an agency that has multiple translators. All their
work is consolidated and added in one invoice for the main contractor, along
with the report on how much money they owe each subcontractor.

This is controlled by optional the ``subcontractors`` user configuration key.


.. _invoices#calculation-currencies:

Currencies
^^^^^^^^^^

Currencies can be set in a user-by-user basis, however this is currently limited
to USD, EUR, CNY and JPY.


.. _invoices#configuring:

Configuring Invoices
--------------------

It's necessary to configure two aspects before proceeding to generate invoices:

* Specify the **users** for whom invoices will be generated, as well as their
  payment details.

  This is detailed in the setting description for
  :setting:`POOTLE_REPORTS_INVOICES_RECIPIENTS`.
* Set the user-specific **payment rates** (per-word, per-review, per-hour) for a
  given period.

  This needs to be set in the *Reports* section of the administration site.
  Select the user from the drop-down and set its rate below. Specific tasks to
  be accounted for payment can also be added manually here.

You may also want to specify the full path to the location where the invoices
will be generated. This is controlled by the
:setting:`POOTLE_REPORTS_INVOICES_DIRECTORY` setting.


.. _invoices#look:

Adjusting the Look & Feel
-------------------------

Before actually sending any invoices, you will want to check how the generated
invoices look like and adjust the layout and styling to match your company's
needs.

The default templates provide a good starting point, so initially you should set
the pre-defined :setting:`POOTLE_REPORTS_INVOICES_COMPANY` and
:setting:`POOTLE_REPORTS_INVOICES_DEPARTMENT` settings to some sensible values
for your use-case and see if the result is of your liking.

Provided you already configured everything by following the previous steps, you
can run ``pootle generate_invoices`` and check for the generated output under
:setting:`POOTLE_REPORTS_INVOICES_DIRECTORY`.

In case you are not satisfied with the look & feel of invoices or their wording
(note the default invoices are in English), you can completely customize the
templates being used by :ref:`copying them to your custom templates location
<customization#templates>` and modifying them at your will. Re-running the
:djadmin:`generate_invoices` command will use them automatically.


.. _invoices#pdfs:

Generating PDFs
---------------

Invoices can optionally be generated in PDF format too, which will also be sent
via e-mail.

PDF generation is performed using `PhantomJS <http://phantomjs.org/>`_. Check
its website and documentation for installation instructions. Once it's available
on your server, you will need to set the absolute path to the ``phantomjs``
binary in the :setting:`POOTLE_REPORTS_INVOICES_PHANTOMJS_BIN` setting and
subsequent runs of :djadmin:`generate_invoices` will generate PDFs as well.


.. _invoices#learn-more:

Learn More
----------

To learn more about invoice generation, check out the command and settings
references.

Commands:

* :djadmin:`generate_invoices`

Settings:

* :setting:`POOTLE_REPORTS_INVOICES_COMPANY`
* :setting:`POOTLE_REPORTS_INVOICES_DEPARTMENT`
* :setting:`POOTLE_REPORTS_INVOICES_DIRECTORY`
* :setting:`POOTLE_REPORTS_INVOICES_PHANTOMJS_BIN`
* :setting:`POOTLE_REPORTS_INVOICES_RECIPIENTS`
