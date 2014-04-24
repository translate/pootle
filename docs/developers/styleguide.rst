.. _styleguide:

Styleguide
==========

Pootle developers try to stick to some development standards that are
gathered in this document.

Python and documentation
------------------------

For Python code and documentation Pootle follows the
:ref:`Translate Styleguide <toolkit:styleguide>` adding extra
clarifications listed below.

- :ref:`Python style conventions <toolkit:styleguide-general>`

- :ref:`Documentation style conventions <toolkit:styleguide-docs>`


Pootle-specific Python guidelines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pootle has specific conventions for Python coding style.


Imports
~~~~~~~

Like in `Python import conventions <toolkit:styleguide-imports>`_ in Translate
styleguide, but imports should be grouped in the following order:

1) __future__ library imports
2) Python standard library imports
3) Third party libraries imports (Including Translate Toolkit ones)
4) Django imports
5) Django external apps imports
6) Other Pootle apps imports
7) Current package (or app) imports, using explicit relative imports (See `PEP
   328 <http://www.python.org/dev/peps/pep-0328/#guido-s-decision>`_)

Check `Python import conventions`_ in Translate styleguide for other
conventions that the imports must follow.

.. code-block:: python

    from __future__ import absolute_import

    import re
    import sys.path as sys_path
    import time
    from datetime import timedelta
    from os import path

    from lxml.html import fromstring
    from translate.storage import versioncontrol

    from django.contrib.auth.models import User
    from django.db import models
    from django.db.models import Q
    from django.db.models.signals import post_save

    from profiles.views import edit_profile
    from tastypie import fields

    from pootle.core.decorators import permission_required
    from pootle_store.models import (FUZZY, TRANSLATED, UNTRANSLATED, Store,
                                     Unit, count_words)
    from pootle_translationproject.models import TranslationProject

    from .forms import GoalForm
    from .models import Tag


Order in models
~~~~~~~~~~~~~~~

Model's inner classes and methods should keep the following order:

- Database fields
- Non database fields
- Default ``objects`` manager
- Custom manager attributes (i.e. other managers)
- ``class Meta``
- ``def natural_key()`` (Because it is tightly related to model fields)
- Properties
- All ``@cached_property`` properties
- Any method decorated with ``@classmethod``
- ``def __unicode__()``
- ``def __str__()``
- Any other method starting with ``__`` (for example ``__init__()``)
- ``def save()``
- ``def delete()``
- ``def get_absolute_url()``
- ``def get_translate_url()``
- Any custom methods


Fields in models and forms
~~~~~~~~~~~~~~~~~~~~~~~~~~

- If the field declaration fits in one line:

  - Put all the options on that line,
  - Don't put a comma after the last option,
  - The parenthesis that closes the field declaration goes just after the last
    option.

- If the field declaration spans to several lines:

  - Each option goes on its own line (including the first one),
  - The options are indented 4 spaces,
  - The last option must have a comma after it,
  - The closing parenthesis in the field declaration goes on its own line,
    aligned with the first line in the field declaration.

.. code-block:: python

    class SampleForm(forms.Form):
        # Field declaration that spans to several lines.
        language = forms.ChoiceField(
            label=_('Interface Language'),
            initial="",
            required=False,
            widget=forms.Select(attrs={
                'class': 'js-select2 select2-language',
            }),
            help_text=_('Default language for using on the user interface.'),
        )
        # One line field declaration.
        project = forms.ModelChoiceField(Project, required=True)


URL patterns
~~~~~~~~~~~~

When writing the URL patterns:

- URL patterns can be grouped by putting a blank line between the groups.
- On each URL pattern:

  - Specify the URL pattern using the ``url()`` function, not a tuple.
  - Each parameter must go on its own line in all cases, indenting them one
    level to allow easily seeing the different URL patterns.
  - In URLs:

    - Use hyphens. Avoid underscores at all costs.
    - To split long URLs use implicit string continuation. Note that URLs are
      raw strings.

- URL pattern names must be named like ``pootle-{app}-{view}`` (except in some
  specific cases):

  - ``{app}`` is the app name, which sometimes can be shortened, e.g. using
    **tp** to avoid the longish **translationproject**. The chosen app name
    must be used consistently across all the URL patterns for the app.
  - ``{view}`` is a unique string which might consist on several words,
    separated with hyphens, that might not match the name of the view that is
    handled by the URL pattern.
  - The exceptions to this naming convention are:

    - URL patterns for AJAX views must be named like ``pootle-xhr-{view}``.
    - URL patterns in *pootle_app* app must be named like:

      - *pootle_app* admin URLs must be named like ``pootle-admin-{view}``
      - Other *pootle_app* URLs must be named like ``pootle-{view}``.

.. code-block:: python

    urlpatterns = patterns('pootle_project.views',
        # Listing of all projects.
        url(r'^$',
            'projects_index'),

        # Whatever URLs.
        url(r'^incredibly-stupid/randomly-long-url-with-hyphens-that-is-split-'
            r'and-continued-on-next-line.html$',
            'whatever',
            name='pootle-project-whatever'),

        # Admin URLs.
        url(r'^(?P<project_code>[^/]*)/admin.html$',
            'project_admin'),
        url(r'^(?P<project_code>[^/]*)/permissions.html$',
            'project_admin_permissions',
            name='pootle-project-admin-permissions'),
    )


Variables naming
~~~~~~~~~~~~~~~~

In order to have a more consistent code the use of specific names for some
heavily used variables is encouraged:

- ``ctx``: Name for the dictionary with the context passed to a template for
  rendering. Also known as *context*, *template variables* or *template vars*.

  .. code-block:: python

    # Good.
    ctx = {
        'language': language,
    }


    # Bad.
    context = {
      ...

    templatevars = {
      ...

    template_vars = {
      ...


Settings naming
~~~~~~~~~~~~~~~

Pootle specific settings must be named like ``POOTLE_*``, for example:
``POOTLE_ENABLE_API``, ``POOTLE_VCS_DIRECTORY`` or ``POOTLE_MARKUP_FILTER``


Pootle-specific documentation guidelines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For documenting several things, Pootle defines custom Sphinx roles.

- Settings::

    .. setting:: PODIRECTORY

  To link to a setting, use ``:setting:`PODIRECTORY```.

- Icons::

    Some reference to |icon:some-icon| in the text.

  This allows you to easily add inline images of icons used in Pootle.
  The icons are all files from :file:`pootle/static/images/sprite`.  If you
  were referring to an icon :file:`icon-edit.png` then you would use the syntax
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

      var $fields = $('.js-search-fields');

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

String
  - A string literal should be wrapped in single quotes.

  - ``join`` should be used to concatenate pieces instead of ``+`` because
    it is usually faster to put the pieces into an array and join them.

Number
  - ``radix`` should be specified in the ``parseInt`` function to
    eliminate reader confusion and to guarantee predictable behavior.

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

Template naming
  - If a template name consists on several words they must be joined using
    underscores (never hyphens), e.g. *my_precious_template.html*

  - If a template is being used in AJAX views, even if it is also used for
    including it on other templates, its name must start with ``xhr_``, e.g.
    *xhr_tag_form.html*.

  - If a template is intended to be included by other templates, and it is not
    going to be used directly, start its name with an underscore, e.g.
    *_included_template.html*.

Quoting
  - Always use double quotes for HTML attribute values.
  - Always use single quotes for Django template tags and template filters
    located inside HTML attribute values.

    .. code-block:: html

        <!-- Good -->
        <a href="{% url 'whatever' %}" class="highlight">



        <!-- Bad -->
        <a href="{% url "whatever" %}" class="highlight">
        <a href='{% url 'whatever' %}' class='highlight'>
        <a href='{% url "whatever" %}' class='highlight'>


CSS
---

Indenting
  - Indent using 4 spaces. Don't use tabs.

  - Put selectors and braces on their own lines.

  - Right-align the CSS browser-prefixed properties.

  Good:

  .. code-block:: css

    .foo-bar,
    .foo-bar:hover
    {
        background-color: #eee;
        -webkit-box-shadow: 0 1px 4px #d9d9d9;
           -moz-box-shadow: 0 1px 4px #d9d9d9;
                box-shadow: 0 1px 4px #d9d9d9;
    }

  Bad:

  .. code-block:: css

    .foo-bar, .foo-bar:hover {
      background-color: #eee;
      -webkit-box-shadow: 0 1px 4px #d9d9d9;
      -moz-box-shadow: 0 1px 4px #d9d9d9;
      box-shadow: 0 1px 4px #d9d9d9;
    }

Naming
  - Selectors should all be in lowercase and consequent words should be
    separated using dashes. As an example, rather use ``.tm-results`` and not
    ``.TM_results``.

.. _1: http://javascript.crockford.com/code.html
.. _2: http://drupal.org/node/172169
.. _3: http://docs.jquery.com/JQuery_Core_Style_Guidelines
