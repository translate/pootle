.. _project_lang_mappings:


Doctest setup...

.. code-block:: python

   >>> getfixture("db_doctest")


Language mapper Configuration
=============================

Language mappings are configured per project using the ``pootle.core.lang_mappers`` key on the
project config, which should be a dictionary of ``upstream_code`` to ``pootle_code`` mappings.

Named presets can also be configured site-wide with the key ``pootle.core.lang_mapping_presets``.

Presets can be used by a ``Project`` by setting ``pootle.core.use_lang_mapping_presets`` on the
``Project`` configuration, with a list containing the name of the preset. ``Project`` configuration
will always override any settings in presets.

Mappings are 1 to 1, and you cannot have 2 upstream codes the same.


Retrieving a lang mapper for a Project
--------------------------------------


.. code-block:: python

   >>> from pootle_project.models import Project
   >>> from pootle.core.delegate import lang_mapper
   >>> project = Project.objects.get(code="project0")
   >>> mapper = lang_mapper.get(Project, instance=project)

There are no custom configs set up so the lang mapper will map pootle_code <> upstream_code exactly.
It can also be used as a dict to retrieve langs for a give upstream_code if they exist


.. code-block:: python

    >>> mapper.get_pootle_code("en")
    'en'
    >>> mapper.get_upstream_code('en')
    'en'
    >>> mapper["en"]
    <Language: English>


Adding a lang mapper configuration
----------------------------------


You can add a custom configuration for the project to map a lang to specific upstream code

.. code-block:: python

    >>> mapper["en_FOO"] is None
    True
    >>> from pootle_config.utils import ObjectConfig
    >>> conf = ObjectConfig(project)
    >>> conf["pootle.core.lang_mapping"] = dict(en_FOO="en")

The mapper caches mapping so we need to get a fresh copy after changing config, and reload the projects
config

.. code-block:: python
		
    >>> project.config.reload()
    >>> mapper = lang_mapper.get(Project, instance=project)
    >>> mapper["en_FOO"]
    <Language: English>
    >>> mapper.get_upstream_code('en')
    u'en_FOO'
    >>> mapper.get_pootle_code('en_FOO')
    u'en'
