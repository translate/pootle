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


Pootle-specific markup
^^^^^^^^^^^^^^^^^^^^^^

For documenting several things, Pootle defines custom Sphinx roles.

- Settings::

    .. setting:: PODIRECTORY

  To link to a setting, use ``:setting:`PODIRECTORY```.

- Icons::

    Some reference to |icon:some-icon| in the text.

  This allows you to easily add inline images of icons used in Pootle.
  The icons are all files from :file:`pootle/static/images/sprite`.  If you
  where refering to an icon :file:`edit.png` then you would use the syntax
  ``|icon:icon-edit|``.  The icon reference is always prefixed by ``icon:``
  and the name of the icon is used without the extension.

  E.g. ``|icon:icon-google-translate|`` will insert this
  |icon:icon-google-translate| icon.




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
    and consequent words should be CamelCased. Never use underscores.

  - If a variable holds a jQuery object, prefix it by a dollar sign ``$``. For
    example:

    .. code-block:: javascript

      var $fields = $(".js-search-fields");

Selectors
  - Prefix selectors that deal with JavaScript with ``js-``. This way it's
    clear the separation between class selectors that deal with presentation
    (CSS) and functionality (JavaScript).

  - Use the same naming criterion as with CSS selector names, ie, lowercase and
    consequent words separated by dashes.

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

Indenting
  - Indent using 2 spaces. Don't use tabs.

  - Although it's desirable to avoid lines longer than 80 characters, most of
    the time the templating library doesn't easily allow this. So try not to
    extend too much the line length.

CSS
---

Indenting
  - Indent using 4 spaces. Don't use tabs.

  - Put selectors and braces on their own lines.

  Good:

  .. code-block:: css

    .foo-bar,
    .foo-bar:hover
    {
        background-color: #eee;
    }

  Bad:

  .. code-block:: css

    .foo-bar, .foo-bar:hover {
      background-color: #eee;
    }

Naming
  - Selectors should all be in lowercase and consequent words should be
    separated using dashes. As an example, rather use ``.tm-results`` and not
    ``.TM_results``.

.. _Translate Styleguide: http://readthedocs.org/docs/translate-toolkit/en/latest/styleguide.html
.. _1: http://javascript.crockford.com/code.html
.. _2: http://drupal.org/node/172169
.. _3: http://docs.jquery.com/JQuery_Core_Style_Guidelines
