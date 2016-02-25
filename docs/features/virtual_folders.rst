.. _virtual_folders:

Virtual Folders
===============

.. versionadded:: 2.7

Virtual folders provide a way to group translations based on any criteria,
including a file across all the languages in a project, or files on specific
locations. Virtual folders have priority, so they can be used to allow
translators to focus on the most important work.


.. _virtual_folders#attributes:

Virtual folders' attributes
---------------------------

Virtual folders have several attributes:

- A mandatory lowercase name,
- A mandatory location,
- An optional priority,
- An optional publicness flag,
- An optional description,
- A field accepting several optional filtering rules.

The location indicates the root place where the virtual folder applies. It can
use placeholders for language (``{LANG}``) and project (``{PROJ}``).

.. note:: The ``/`` location is not valid and must be replaced by
    ``/{LANG}/{PROJ}/``. The locations starting with ``/projects/`` are also
    not valid and must be changed so they instead start with ``/{LANG}/``.


Each virtual folder must have a unique combination of name and location. This
means that there can exist two different virtual folders with the same name if
they have different locations.

The priority defaults to ``1`` and accepts any value greater than ``0``,
including numbers with decimals, like ``0.75``. Higher numbers means higher
priority.

By default virtual folders are public. If they are not public then they won't
be displayed, but they are still used for sorting.

Also the virtual folders can have a description which might be useful to
explain the contents of the folder or provide additional instructions. This
might be handy when using the virtual folders as goals.

The filtering rules specify which translation units are included within a
virtual folder. Currently the only supported filtering rule consists of a list
of file or directory paths relative to the virtual folder location. Note
that it is required to set some filtering rule.


.. _virtual_folders#apply:

Adding and updating virtual folders
-----------------------------------

To add or modify the properties of virtual folders use the
:djadmin:`add_vfolders` management command.

This command imports a JSON file holding a list of virtual folders, and the
files included on each virtual folder along with all their attributes. Check
the specs for the :ref:`JSON format <virtual_folders#json-format>` in order to
know how to craft a JSON file that fits your needs.


.. _virtual_folders#stats:

Calculating virtual folders stats
---------------------------------

To calculate the translation stats of virtual folders use the
:djadmin:`refresh_stats` management command. Virtual folder stats will be
calculated along regular directories and files stats.

After the initial calculation no extra runs will be required unless virtual
folders are changed by a run of the :djadmin:`add_vfolders` management command.
Changes introduced due to translation through the editor will automatically
update the stats without intervention.


.. _virtual_folders#translate:

Translating virtual folders
---------------------------

If a virtual folder applies in the current location, then clicking on the links
on the overview page will provide the units in priority order when translating
in the editor. The priority sorting on the translation editor is calculated
taking into account all the applicable virtual folders in the current location,
including the not public ones.


.. _virtual_folders#json-format:

Format for the JSON file
------------------------

The JSON file used to import virtual folders consists of a list of virtual
folder definitions with the :ref:`same fields <virtual_folders#attributes>` as
the virtual folders, except for two differences:

- If the **description** includes newlines those must be escaped.

The following example depicts a basic JSON file:

.. literalinclude:: virtual_folders.json
   :language: json
