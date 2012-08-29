.. _styleguide:

Styleguide
==========

Pootle developers try to stick to some development standards that are
gathered in this document.

Python and documentation
------------------------

For Python code and documentation Pootle follows the
:ref:`Translate Styleguide <toolkit:styleguide>`.

- :ref:`Python style conventions <toolkit:styleguide-general>`

- :ref:`Documentation style conventions <toolkit:styleguide-docs>`

JavaScript
----------

There are no "official" coding style guidelines for JavaScript, so based
on several recommendations (`1`_, `2`_, `3`_) we try to stick to our
preferences.

Indenting
  - We currently use 2-space indentation. Don't use tabs.

  - Avoid lines longer than 80 characters. When a statement will not fit
    on a single line, it may be necessary to break it. Place the break
    after an operator, ideally after a comma.

Whitespace
  - If a function literal is anonymous, there should be one space between
    the word ``function`` and the ``(`` (left parenthesis).

  - In function calls, don't use any space before the ``(`` (left parenthesis).

  - Control statements should have one space between the control keyword
    and opening parenthesis, to distinguish them from function calls.

  - Each ``;`` (semicolon) in the control part of a ``for`` statement should
    be followed with a space.

  - Whitespace should follow every ``,`` (comma).

Naming
  - Variable and function names should always start by a lowercase letter
    and consequent words should be CamelCased.

Control statements
  Control statements such as ``if``, ``for``, or ``switch`` should follow
  these rules:

  - The enclosed statements should be indented.

  - The ``{`` (left curly brace) should be at the end of the line that
    begins the compound statement.

  - The ``}`` (right curly brace) should begin a line and be indented
    to align with the beginning of the line containing the matching
    ``{`` (left curly brace).

  - Braces should be used around all statements, even single statements,
    when they are part of a control structure, such as an ``if`` or ``for``
    statement. This makes it easier to add statements without accidentally
    introducing bugs.

  - Should have one space between the control keyword and opening
    parenthesis, to distinguish them from function calls.

Examples
  - ``if`` statements

    .. code-block:: javascript

      if (condition) {
        statements
      }

      if (condition) {
        statements
      } else {
        statements
      }

      if (condition) {
        statements
      } else if (condition) {
        statements
      } else {
        statements
      }

  - ``for`` statements

    .. code-block:: javascript

      for (initialization; condition; update) {
        statements;
      }

      for (variable in object) {
        if (condition) {
          statements
        }
      }

  - ``switch`` statements

    .. code-block:: javascript

      switch (condition) {
        case 1:
          statements
          break;

        case 2:
          statements
          break;

        default:
          statements
      }

HTML
----

CSS
---

.. _Translate Styleguide: http://readthedocs.org/docs/translate-toolkit/en/latest/styleguide.html
.. _1: http://javascript.crockford.com/code.html
.. _2: http://drupal.org/node/172169
.. _3: http://docs.jquery.com/JQuery_Core_Style_Guidelines
