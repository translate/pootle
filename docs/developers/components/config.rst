#doctest: +ELLIPSIS
.. _plugin_config:


Doctest setup...

.. code-block:: python

   >>> getfixture("db_doctest")


Plugin Configuration
====================


You can get and set configuration options using Pootle's config app.

Using this system, configuration can be set at 3 levels

- System-wide
- Per-model
- Per-object

Keys do not have to be unique and are a maximum of 255 chars.

Values are stored as JSON strings, so can be any JSON-serializable value.


Retrieving a configuration object
---------------------------------

.. code-block:: python

   >>> from pootle.core.delegate import config
   >>>
   >>> config.get()
   []

.. code-block:: python

   >>> from pootle_project.models import Project
   >>>
   >>> config.get(Project)
   []

.. code-block:: python

   >>> project = Project.objects.first()
   >>> config.get(Project, instance=project)
   []

.. code-block:: python

   >>> type(config.get())
   <class 'pootle_config.managers.ConfigQuerySet'>

.. code-block:: python

   >>> config.get().filter(key="foo")
   []


Setting configuration
---------------------

.. code-block:: python

   >>> config.get().set_config("foo", "global bar")
   >>> config.get().get_config("foo")
   u'global bar'


.. code-block:: python

   >>> config.get(Project).set_config("foo", "model bar")
   >>> config.get(Project).get_config("foo")
   u'model bar'


.. code-block:: python

   >>> config.get(Project, instance=project).set_config("foo", "instance bar")
   >>> config.get(Project, instance=project).get_config("foo")
   u'instance bar'


.. code-block:: python

   >>> config.get(Project, instance=project).set_config("foo", "bar2")
   >>> config.get(Project, instance=project).get_config("foo")
   u'bar2'



Appending configuration
-----------------------

.. code-block:: python

   >>> config.get(Project).append_config("appended_foo", "appending1")
   >>> config.get(Project).append_config("appended_foo", "appending1")


.. code-block:: python

   >>> config.get(Project).append_config("appended_foo", "appending2")
   >>> config.get(Project).append_config("appended_foo", "appending3")

.. code-block:: python

   >>> config.get(Project).get_config("appended_foo")
   Traceback (most recent call last):
   ...
   MultipleObjectsReturned: get() returned more than one Config -- it returned 4!


.. code-block:: python

   >>> config.get(Project).set_config("appended_foo", "something else")
   Traceback (most recent call last):
   ...
   MultipleObjectsReturned: get() returned more than one Config -- it returned 4!



Getting configuration
---------------------

.. code-block:: python

   >>> config.get().get_config("foo")
   u'global bar'
   >>> config.get(Project).get_config("foo")
   u'model bar'
   >>> config.get(Project, instance=project).get_config("foo")
   u'bar2'



Listing configuration
---------------------

.. code-block:: python

   >>> config.get(Project).list_config("appended_foo")
   [(u'appended_foo', u'appending1'), (u'appended_foo', u'appending1'), (u'appended_foo', u'appending2'), (u'appended_foo', u'appending3')]


Queryset chaining
-----------------

.. code-block:: python

   >>> config.get().set_config("global_foo", "bar")
   >>> config.get().none().get_config("global_foo")
   u'bar'

.. code-block:: python

   >>> config.get(Project).set_config("project_foo", "bar2")
   >>> config.get(Project).none().get_config("project_foo")
   u'bar2'

.. code-block:: python

   >>> config.get(Project).none().query_model
   <class 'pootle_project.models.Project'>

.. code-block:: python

   >>> project == config.get(Project, instance=project).none().query_model
   True


Validating configuration before saving
--------------------------------------

.. code-block:: python

   >>> from django.core.exceptions import ValidationError

   >>> from pootle.core.plugin import getter
   >>> from pootle_config.delegate import (
   ...     config_should_not_be_set, config_should_not_be_appended)

   >>> @getter([config_should_not_be_set, config_should_not_be_appended])
   ... def list_config_validator(**kwargs):
   ...     if kwargs["key"] == "foo":
   ...         if not isinstance(kwargs["value"], list):
   ...             return ValidationError(
   ...                 "Config '%s' must be a list" % kwargs["key"])


.. code-block:: python

   >>> @getter(config_should_not_be_appended, sender=Project)
   ... def unique_config_validator(**kwargs):
   ...     conf = config.get(Project, instance=kwargs["instance"])
   ...     if conf.get_config(kwargs["key"]) is not None:
   ...         return ValidationError(
   ...             "Config keys for '%s' must be unique" % kwargs["sender"])


Storing JSON data
-----------------

Lists are stored as lists

.. code-block:: python

   >>> config.get().set_config("jsonlist", [1, 2, 3])
   >>> config.get().get_config("jsonlist")
   [1, 2, 3]

Tuples are stored as lists

.. code-block:: python

   >>> config.get().set_config("jsontuple", (4, 5, 6))
   >>> config.get().get_config("jsontuple")
   [4, 5, 6]

Dictionaries are stored as ``OrderedDict``

.. code-block:: python

   >>> config.get().set_config("jsondict", dict(a=1, b=2, c=3))
   >>> type(config.get().get_config("jsondict"))
   <class 'collections.OrderedDict'>

If you want to ensure the ordering of a dictionary, you must pass an ``OrderedDict`` to config.

.. code-block:: python

   >>> from collections import OrderedDict

   >>> config.get().set_config("jsonorderdict", OrderedDict((("a", 1), ("b", 2), ("c", 3))))
   >>> config.get().get_config("jsonorderdict")
   OrderedDict([(u'a', 1), (u'b', 2), (u'c', 3)])


Catching Config object errors
-----------------------------

.. code-block:: python

   >>> conf = config.get(Project)
   >>> try:
   ...     conf.get_config("appended_foo")
   ... except conf.model.MultipleObjectsReturned:
   ...     print("Too many objects!")
   Too many objects!



Using SiteConfig utility object
-------------------------------

You can use config utility objects to treat site, model and object config as python dictionaries.

To retrieve site configuration you can do the following

.. code-block:: python

   >>> from pootle_config.utils import SiteConfig
   >>> site_conf = SiteConfig()
   >>> site_conf
   <pootle_config.utils.SiteConfig object at ...>

You can then use it as a python dictionary to retrieve config keys, items and values

If config has been appended it will use the value of the last config item with the shared key.

As we did not append any site config, the dictionary matches the values provided by ``list_config``

.. code-block:: python

   >>> site_conf.items() == config.get().list_config()
   True

   >>> site_conf.keys() == [c[0] for c in config.get().list_config()]
   True

   >>> site_conf.values() == [c[1] for c in config.get().list_config()]
   True


And you can retrieve individual keys like so.

.. code-block:: python

   >>> site_conf["foo"]
   u'global bar'


And set keys

.. code-block:: python

   >>> site_conf["another_key"] = "another_value"
   >>> site_conf["another_key"]
   u'another_value'

   >>> site_conf["another_key"] = "and_another_value"
   >>> site_conf["another_key"]
   u'and_another_value'

   >>> SiteConfig()["another_key"]
   u'and_another_value'


Using ModelConfig utility object
--------------------------------

You can use config utility objects to treat site, model and object config as python dictionaries.

To retrieve model configuration you can do the following

.. code-block:: python

   >>> from pootle_config.utils import ModelConfig
   >>> model_conf = ModelConfig(Project)
   >>> model_conf
   <pootle_config.utils.ModelConfig object at ...>

You can then use it as a python dictionary to retrieve config keys, items and values

.. code-block:: python

   >>> set(model_conf.keys()) == set([c[0] for c in config.get(Project).list_config()])
   True


And you can retrieve individual keys like so.

.. code-block:: python

   >>> model_conf["foo"]
   u'model bar'


If the key was appended, we will get value from the last one appended

   >>> model_conf["appended_foo"]
   u'appending3'


And set keys

.. code-block:: python

   >>> model_conf["another_key"] = "another_value"
   >>> model_conf["another_key"]
   u'another_value'

   >>> model_conf["another_key"] = "and_another_value"
   >>> model_conf["another_key"]
   u'and_another_value'

   >>> ModelConfig(Project)["another_key"]
   u'and_another_value'
