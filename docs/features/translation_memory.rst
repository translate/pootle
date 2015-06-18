.. _translation_memory:

Translation Memory
==================

Pootle provides suggested translations to the current string.  Translator can
use these suggestions as their translation or to aid their translation.

Suggestions are based on previous translations of similar strings.  These
Translation Memory (TM) matches mean that you can speed up your translation and
ensure consistency across your work.


.. _translation_memory#using_translation_memory:

Using Translation Memory
------------------------

Translation Memory suggestions are automatically retrieved when you enter a new
translation unit. These are displayed below the editing widget.  You can insert
a TM suggestion by clicking on the suggestion row.

The differences between the current string and the suggested string are
highlighted, this allows you to see how the two differ and helps you make
changes to the suggestion to make it work as the current translation.


.. _translation_memory#configuring_translation_memory:

Configuring Translation Memory
------------------------------

Translation Memory will work out of the box with a default Pootle installation.
There are two methods of getting Translation Memory.

1. Amagama - for remote Translation Memory
2. Elasticsearch - for local Translation Memory

Amagama based remote TM
~~~~~~~~~~~~~~~~~~~~~~~

By default Pootle will query Translate's `Amagama
<http://amagama.translatehouse.org>`_ Translation Memory server, which hosts
translations of an extensive collection of Opensource software.

If you want to setup and connect to your own TM server then the
:setting:`AMAGAMA_URL` will allow you to point to a private TM server.


.. _translation_memory#local_translation_memory:

Elasticsearch based local TM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2.7

By default this is configured to operate if local TM is available.  To use it
you will need to install `Elasticsearch 
<https://www.elastic.co/products/elasticsearch>`_ and populate the initial
translation memory using the :djadmin:`update_tmserver` command:

.. code-block:: bash

   (env) $ pootle update_tmserver


Once populated Pootle will keep Local TM up-to-date.

.. note:: Note that Elasticsearch depends on Java.


Local TM settings can be adjusted in :setting:`POOTLE_TM_SERVER`.

You may want to disable Amagama by setting :setting:`AMAGAMA_URL` to ``''`` if
you are using Elasticsearch local TM, though the two will operate together.
