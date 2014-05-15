.. _maintenance:

Temporarily disable Pootle for maintenance
==========================================

.. versionadded:: 2.5.2

In large Pootle deployments usually the administrators need to temporarily
disable the server to perform maintenance tasks without the interference of the
users while displaying a *We will be back soon* notice. Pootle allows to
accomplish such tasks by disabling the site using the `django-maintenancemode
<https://pypi.python.org/pypi/django-maintenancemode>`_ app.

The site can be easily disabled by specifying the following in Pootle settings:

.. code-block:: python

  MAINTENANCE_MODE = True


Have in mind that the administrators that are already logged in will be able to
use Pootle as if it wasn't disabled for maintenance.


.. note:: Users accessing Pootle from IPs listed is in the
   :option:`INTERNAL_IPS` setting won't see the maintenance notice, and thus
   will be able to normally use Pootle.


.. note:: If you need to enable specific URLs in your Pootle server then you
   can use the :option:`MAINTENANCE_IGNORE_URLS` setting to specify such URLs.
   Please refer to `django-maintenancemode homepage
   <https://github.com/shanx/django-maintenancemode>`_ for more information.
