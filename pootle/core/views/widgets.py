# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.forms import CheckboxInput, Select, SelectMultiple
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.safestring import SafeText, mark_safe


class TableSelectMultiple(SelectMultiple):
    """
    Provides selection of items via checkboxes, with a table row
    being rendered for each item, the first cell in which contains the
    checkbox.

    When providing choices for this field, give the item as the second
    item in all choice tuples. For example, where you might have
    previously used::

        field.choices = [(item.id, item.name) for item in item_list]

    ...you should use::

        field.choices = [(item.id, item) for item in item_list]
    """

    def __init__(self, item_attrs, *args, **kwargs):
        """
        item_attrs
            Defines the attributes of each item which will be displayed
            as a column in each table row, in the order given.

            Any callables in item_attrs will be called with the item to be
            displayed as the sole parameter.

            Any callable attribute names specified will be called and have
            their return value used for display.

            All attribute values will be escaped.
        """
        super(TableSelectMultiple, self).__init__(*args, **kwargs)
        self.item_attrs = item_attrs

    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = []
        # Normalize to strings.
        str_values = set([force_text(v) for v in value])
        for i, (option_value, item) in enumerate(self.choices):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
            cb = CheckboxInput(
                final_attrs,
                check_test=lambda value: value in str_values)
            option_value = force_text(option_value)
            rendered_cb = cb.render(name, option_value)
            output.append(u'<tr>')
            output.append(u'<td class="row-select">%s</td>' % rendered_cb)
            for attr in self.item_attrs:
                css_name = attr
                if callable(attr):
                    content = attr(item)
                    css_name = attr.__name__.strip("_")
                elif hasattr(item, attr):
                    if callable(getattr(item, attr)):
                        content = getattr(item, attr)()
                    else:
                        content = getattr(item, attr)
                else:
                    content = item[attr]
                if not isinstance(content, SafeText):
                    content = escape(content)
                css = (
                    ' class="field-%s"'
                    % css_name.lower().replace("_", "-").replace(" ", "-"))
                output.append(u'<td%s>%s</td>' % (css, content))
            output.append(u'</tr>')
        return mark_safe(u'\n'.join(output))


class RemoteSelectWidget(Select):

    def render_options(self, selected_choices):
        return ""
