.. _plugins:

Plugins
=======

.. warning::

   Pootle's plugin system is currently in an early stage of development, and
   may be subject to change in the future. If you have any questions or are
   intending to use it in your own applications you can chat with us on the
   `Translate development channel <https://gitter.im/translate/dev>`_.


You can customize or extend Pootle using plugins.

A Pootle plugin is a Django application that hooks into
the core functionality in Pootle.


.. _plugins#signals-providers-getters:

Signals, providers and getters
------------------------------

Pootle emits ``Signals`` when key events happen. You can listen to these
signals using a ``receiver`` to trigger custom behaviour. Pootle uses
Django's Signals framework for handling these types of events.

Pootle allows plugins to override the default behaviour using a ``Getter``
function, which are decorated with the ``pootle.core.plugin.getter`` decorator.
Once Pootle has received a response from a plugin for a ``Getter`` function
it stops processing any further configured functions.

Pootle allows developers to change or extend the data used by the system,
by adding ``Provider`` functions, which are decorated with the
``pootle.core.plugin.provider`` decorator. With ``Provider`` functions Pootle
will gather data from all plugins configured to provide for a given
``Provider`` function.


.. _plugins#basic-file-structure:

Application file structure
--------------------------

- :file:`__init__.py`
- :file:`apps.py` - Django application configuration
- :file:`receivers.py` - receivers for signals
- :file:`getters.py` - getter functions
- :file:`providers.py` - provider functions


.. _plugins#creating-a-plugin:

Creating a plugin application
-----------------------------

Your application requires a `Django application configuration
<https://docs.djangoproject.com/es/1.9/ref/applications/#for-application-authors>`_

For an application named ``pootle_custom`` you need to add lines similar to the
following in the :file:`__init__.py`:


.. code-block:: python

   default_app_config = 'pootle_custom.apps.PootleCustomConfig'


With the above configuration you should add an :file:`apps.py`.

At a minimum this should define the ``PootleCustomConfig`` class with its
``name`` and ``verbose_name``.

It can also be used to activate receivers, providers and getters. The following
application configuration activates all of them for the "custom" application.

.. code-block:: python

   import importlib

   from django.apps import AppConfig


   class PootleCustomConfig(AppConfig):

       name = "pootle_custom"
       verbose_name = "Pootle Custom"

       def ready(self):
           importlib.import_module("pootle_custom.receivers")
           importlib.import_module("pootle_custom.providers")
           importlib.import_module("pootle_custom.getters")


.. _plugins#providers:

Setting up a provider
---------------------

The following is an example of providing custom ``context_data`` to the Pootle
``LanguageView``.

Add a file called :file:`providers.py` with the following:

.. code-block:: python

   from pootle.core.delegate import context_data
   from pootle.core.plugin import provider

   from pootle_language.views import LanguageView


   @provider(context_data, sender=LanguageView)
   def provide_context_data(**kwargs):
       return dict(
           custom_var1="foo",
	   custom_var2="bar")



.. _plugins#getters:

Setting up a getter
-------------------

The following is an example of customizing the ``Unit`` ``search_backend`` for an
application.

Add a file called :file:`getters.py` with the following:

.. code-block:: python

   from pootle.core.delegate import search_backend
   from pootle.core.plugin import getter

   from pootle_store.models import Unit
   from pootle_store.unit.search import DBSearchBackend


   class CustomSearchBackend(DBSearchBackend):
       pass


   @getter(search_backend, sender=Unit)
   def get_search_backend(**kwargs):
       return CustomSearchBackend



.. _plugins#receivers:

Setting up a receiver
---------------------

Pootle uses the `django.core.signals
<https://docs.djangoproject.com/en/1.9/topics/signals/#connecting-receiver-functions>`_
module to handle events.

The following is an example of a ``receiver`` that emits a log warning whenever
a ``Store`` cache is expired.

Add a file called :file:`receivers.py` with the following code:

.. code-block:: python

   import logging

   from django.core.signals import receiver

   from pootle.core.signals import cache_cleared
   from pootle_store.models import Store


   @receiver(cache_cleared, sender=Store)
   def handle_cache_cleared(**kwargs):
       logging.warn(
           "Store cache cleared: %s"
	   % kwargs["instance"].pootle_path)
