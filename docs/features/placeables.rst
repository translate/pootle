.. _placeables:

Placeables
**********

.. versionadded:: 2.5.2

Placeables are special parts of the text that can be automatically highlighted
and easily inserted into the translation. By using placeables, a translator can
avoid certain errors, such as retyping numbers or acronyms incorrectly, or
perhaps introducing an error when retyping some program codes, such as XML.
Pootle will help you to insert these placeables easily, and save you time
because you don't have to type them.

Pootle will visually highlight the placeables that it recognises in the text.


.. image:: /_static/placeables.png


Some examples of placeables that Pootle can help you with are:

- Numbers
- Acronyms
- XML
- E-mail addresses
- URLs
- Variables used in software localization
- Inline tags in XLIFF files


.. _placeables#selecting_and_inserting:

Selecting and Inserting
=======================

Placeables can be handled using either the mouse or the keyboard.

When inserting a placeable it will be automatically inserted on the target
field where the cursor is. If no cursor is present then it will inserted at the
beginning of the text in the target field.

To insert a given placeable using the mouse just click on it.

To insert a placeable using the keyboard it is necessary to first select it.
After inserting a placeable the next one will be automatically selected. See
the :ref:`Keyboard shortcuts reference <shortcuts#editing>` for the shortcuts
used to manipulate placeables.
