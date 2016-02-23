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
There are three methods of getting Translation Memory.

1. Amagama - for remote Translation Memory
2. Elasticsearch - for local Translation Memory
3. Elasticsearch - for external Translation Memory


.. _translation_memory#amagama:

Amagama based remote TM
~~~~~~~~~~~~~~~~~~~~~~~

By default Pootle will query Translate's `Amagama
<http://amagama.translatehouse.org>`_ Translation Memory server, which hosts
translations of an extensive collection of Opensource software.

If you want to setup and connect to your own TM server then the
:setting:`AMAGAMA_URL` will allow you to point to a private TM server.


.. _translation_memory#elasticsearch_based_tms:

Elasticsearch-based TMs
~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2.7

Pootle can also retrieve TM matches stored on Elasticsearch-based TM servers.
These TM servers require
`Elasticsearch <https://www.elastic.co/products/elasticsearch>`_ to be
installed and running.

.. note:: Elasticsearch depends on Java. Note that some systems may ship with
  OpenJDK, however `elasticsearch recommends using Oracle JDK
  <https://www.elastic.co/guide/en/elasticsearch/reference/1.6/setup-service.html#_installing_the_oracle_jdk>`_.


Pootle supports two types of Elasticsearch-based TMs:

- **Local TM**: (just one, named ``local``) is populated using translations
  stored in Pootle database and every new translation gets automatically
  imported to it.

- **External TMs**: (several) are populated from translation files specifically
  provided by the server admins, and are not automatically updated.


Both local and external TM settings can be adjusted in
:setting:`POOTLE_TM_SERVER`. A configuration example for local and external TM
can be found in the default :file:`~/.pootle/pootle.conf`, and can be enabled by
uncommenting the example.

Please see the :setting:`POOTLE_TM_SERVER-WEIGHT` for a full example of the
configuration necessary to set up local/external TM.

You may want to disable Amagama by setting :setting:`AMAGAMA_URL` to ``''`` if
you are using Elasticsearch-based TMs, though both can operate together.


.. _translation_memory#local_translation_memory:

Elasticsearch-based local TM
++++++++++++++++++++++++++++

.. versionadded:: 2.7

To use it, the ``local`` TM must be enabled on :setting:`POOTLE_TM_SERVER` and
will need to be populated using the :djadmin:`update_tmserver` command:

.. code-block:: console

   (env) $ pootle update_tmserver


Once populated Pootle will keep Local TM up-to-date.


.. _translation_memory#external_translation_memories:

Elasticsearch-based external TMs
++++++++++++++++++++++++++++++++

.. versionadded:: 2.7.3

In order to use them they must be enabled on :setting:`POOTLE_TM_SERVER` and
you will need to populate them using the :djadmin:`update_tmserver` command
specifying the TM to use with :option:`--tm <update_tmserver --tm>` and the
display name with :option:`--display-name <update_tmserver --display-name>`:

.. code-block:: console

   (env) $ pootle update_tmserver --tm=external --display-name=Pidgin af.po gl.tmx


A display name is a label used to group translations within a TM. A given TM
can host translations for several labels. Just specify them with
:option:`--display-name <update_tmserver --display-name>`:

.. code-block:: console

   (env) $ pootle update_tmserver --tm=external --display-name=GNOME pt.tmx eu.po xh.po


It is possible to have several Elasticsearch-based external TM servers working
at once, along with the Elasticsearch-based local TM server. In order to do so
just add new entries to :setting:`POOTLE_TM_SERVER`:

.. code-block:: python

    POOTLE_TM_SERVER = {

        ...

        'libreoffice': {
            'ENGINE': 'pootle.core.search.backends.ElasticSearchBackend',
            'HOST': 'localhost',
            'PORT': 9200,
            'INDEX_NAME': 'whatever',
            'WEIGHT': 0.9,
            'MIN_SCORE': 'AUTO',
        },
    }

Make sure :setting:`INDEX_NAME <POOTLE_TM_SERVER-INDEX_NAME>` is unique. You
might also want to tweak :setting:`WEIGHT <POOTLE_TM_SERVER-WEIGHT>` to change
the score of the TM results in relation to other TM servers (valid values are
between ``0.0`` and ``1.0``).

To use these additional external TMs you will need to populate them using the
:djadmin:`update_tmserver` command specifying the TM server with :option:`--tm
<update_tmserver --tm>`:

.. code-block:: console

   (env) $ pootle update_tmserver --tm=libreoffice --display-name=LibreOffice af.po gl.tmx


Check :djadmin:`update_tmserver` for more options.

Note that Pootle will not push new translations to these TM servers unless you
explicitly use the :djadmin:`update_tmserver` command, giving you full control
of which translations make into them.
