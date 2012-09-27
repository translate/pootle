.. _customization:

Customizing the look
====================

In some cases it might be desirable to customize the styling of Pootle to fit
in with your other websites or other aspects of your identity. It might also be
required to add a common header or footer for proper visual integration. Before
you start editing the CSS of Pootle, have a look at our `styling guidelines for
developers <http://translate.sourceforge.net/wiki/developers/styling>`_.

Custom changes are kept separate from the distributed files, so that upgrades
are unlikely to affect your customizations.


.. _customization#css:

Customizing CSS
---------------

Edit the file in *static/css/custom/custom.css* to override any rules from the
main CSS file. That CSS file will be included in every page.


.. _customization#images:

Customizing images
------------------

Any custom images can be placed in *static/css/custom/*. The *custom.css* file
can refer to it directly by name, without having to specify a path, since it is
in the same directory.


.. _customization#favicon:

Customizing the favicon
-----------------------

The favicon can be customized by editing the base template directly
*templates/base.html*). This has the downside that you have to reimplement this
on upgrades if the base template is replaced. Alternatively the base template
can be overridden as a whole with the favicon customized to your needs (see the
next section).


.. _customization#templates:

Customizing templates
---------------------

In case you need to change a template, copy it into *templates/custom/* with
the same name as it had before. Make sure that you have a complete copy of the
template and then make any changes you require.

If you edit any templates, keep in mind that any changes to the text could
result in untranslated text for users of the non-English user interface.

On upgrades, it would be ideal to ensure that any changes to the distributed
templates are reflected in your customized versions of them, to ensure all
features and improvements are present.
