.. _translation_memory:

Translation Memory
==================

.. versionchanged:: 2.5

Pootle provides suggested translations to the current string.  Translator can
use these suggestions for the translation.

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
There are two source for Translation Memory in Pootle:

1. Local Translation Memory
2. Remote Translation Memory

Local Translation Memory
^^^^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 2.5.2

Local Translation Memory is served from Pootle itself.  All projects hosted on
Pootle are available to give TM suggestions to translators.

This allows translations that have just been submitted to be served as
suggestions immediately.

Local Translation Memory can also serve icons representing the source of the
suggestion.  When you know where a translation came from it is easier to
evaluate its usefulness. These icons are stored in :setting:`PODIRECTORY`
``/$project/.pootle/icon.png``

Remote Translation Memory
^^^^^^^^^^^^^^^^^^^^^^^^^

Pootle will query Translate's `Amagama <http://amagama.translatehouse.org>`_
Translation Memory server, which hosts translations of an extensive collection
of Opensource software.  Thus with no effort you have access to a very large
database of Translation Memory results for many languages.

If you want to setup and connect to your own TM server rather than Translate's
hosted Amagama server then the :setting:`AMAGAMA_URL` will allow you to point
to your private TM server.
