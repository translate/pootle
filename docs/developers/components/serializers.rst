.. _serializers:


Doctest setup...

.. code-block:: python

   >>> getfixture("db_doctest")


Serializers
===========

You can customize the serialization to and from Stores in Pootle.

This allows you to make formatting or other changes before saving to disk, and
conversely you can make changes to files before importing into Pootle.

Serializers and deserializers defined in plugins can be configured for projects using
`django-admin`:"config".

This document explains how to write custom serializers and deserializers in a Pootle
plugin application.


.. _serializers#custom-serializer:

Adding a custom serializer
--------------------------

Lets add a `CustomSerializer`

.. code-block:: python

   >>> from pootle.core.serializers import Serializer

   >>> class CustomSerializer(Serializer):
   ... 
   ...     @property
   ...     def output(self):
   ...         if self.context.id % 2:
   ...             return "X%sX" % self.original_data
   ...         return self.original_data


The serializer class will be called with 2 arguments, `context` which is a ``Store``,
 and ``original_data`` containing the data to serialize. 

The original data is a bare representation of the Store according to the `Project`'s
`localfiletype`, unless the data has already been through another serialization filter
already.

The serializer class should implement a property called `output`, which should
return the modified data.

In this example, we add and `X` to the start and end of the data to be serialized.

Serializers can make minor formatting changes, or they can change the structure
of the document. If the content is changed in such a way that ttk will parse
the result differently, then a matching deserializer will likely be required.


.. _serializers#custom-deserializer:

Adding a custom deserializer
----------------------------


Lets add a `CustomDeserializer`

.. code-block:: python

   >>> from pootle.core.serializers import Deserializer

   >>> class CustomDeserializer(Deserializer):
   ... 
   ...     @property
   ...     def output(self):
   ...         if self.context.id % 2:
   ...             return self.original_data.strip("X")
   ...         return self.original_data


As with serializers, deserializers are called with `context` which is the `Store` being
deserialized, and `original_data` which is the data to deserialize.


.. _serializers#serializer-providers:

Add a provider file to enable your serializers
----------------------------------------------

To enable serializers you will need to add a provider function
for `pootle.core.delegate.serializers`.

Serializers are named, and the provider function should return
a dictionary of serializer classes, using the serializer names
as the dictionary keys.


.. code-block:: python

   >>> from pootle.core.delegate import serializers
   >>> from pootle.core.plugin import provider
   >>> from pootle_project.models import Project

   >>> @provider(serializers, sender=Project)
   ... def provide_serializers(**kwargs):
   ...     return dict(custom_serializer=CustomSerializer)


.. _serializers#deserializer-providers:

Enabling your deserializers
---------------------------

To enable deserializers you will need to add a provider function
for `pootle.core.delegate.deserializers`.

Deserializers are named, and the provider function should return
a dictionary of deserializer classes, using the deserializer names
as the dictionary keys.

If necessary, add a file called `providers.py`. To enable our CustomSerializer
we will need something like the following in the providers file


.. code-block:: python

   >>> from pootle.core.delegate import deserializers
   >>> from pootle.core.plugin import provider
   
   >>> @provider(deserializers, sender=Project)
   ... def provide_deserializers(**kwargs):
   ...     return dict(custom_deserializer=CustomDeserializer)


Configuring a ``Project``
-------------------------


Once your de/serializers are setup you will need to configure them for any
project that needs to use them

.. code-block:: python

   >>> from django.db.models import F
   >>> from pootle_config.utils import ObjectConfig
   >>> from pootle_store.models import Store

   >>> project = Project.objects.get(code="project0")
   >>> conf = ObjectConfig(project)
   >>> from pootle.core.delegate import serializers
   >>> conf["pootle.core.serializers"] = ["custom_serializer"]

Now odd numbered stores will get the `X` appended and prepended.

.. code-block:: python

   >>> stores = Store.objects.filter(translation_project__project=project)
   >>> odd_store = stores.annotate(odd=F('id') % 2).filter(odd=1).first()
   >>> odd_store.serialize()[0]
   'X'
   >>> odd_store.serialize()[-1]
   'X'

But the even numbered stores dont

.. code-block:: python

   >>> even_store = stores.annotate(odd=F('id') % 2).filter(odd=0).first()
   >>> even_store.serialize()[0] == 'X'
   False
   >>> even_store.serialize()[-1] == 'X'
   False


Deserializing the odd numbered store strips the `X` s.

.. code-block:: python

   >>> serialized = odd_store.serialize()
   >>> conf["pootle.core.deserializers"] = ["custom_deserializer"]
   >>> deserialized = odd_store.deserialize(serialized)
   >>> deserialized
   <translate.storage.pypo.pofile object at ...>

   >>> assert str(deserialized) == serialized[1:-1]
