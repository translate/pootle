#
# djblets_utils.py -- Various utility template tags
#
# Copyright (c) 2007-2008  Christian Hammond
# Copyright (c) 2007-2008  David Trowbridge
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import datetime
import os

from django import template
from django.template import TemplateSyntaxError
from django.template.defaultfilters import stringfilter
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from djblets.util.decorators import basictag, blocktag


register = template.Library()


@register.tag
@blocktag
def definevar(context, nodelist, varname):
    """
    Defines a variable in the context based on the contents of the block.
    This is useful when you need to reuse the results of some tag logic
    multiple times in a template or in a blocktrans tag.
    """
    context[varname] = nodelist.render(context)
    return ""


@register.tag
@blocktag
def ifuserorperm(context, nodelist, user, perm):
    """
    Renders content depending on whether the logged in user is the specified
    user or has the specified permission.

    This is useful when you want to restrict some code to the owner of a
    review request or to a privileged user that has the abilities of the
    owner.

    Example::

        {% ifuserorperm myobject.user "myobject.can_change_status" %}
        Owner-specific content here...
        {% endifuserorperm %}
    """
    req_user = context.get('user', None)
    if user == req_user or req_user.has_perm(perm):
        return nodelist.render(context)

    return ''


@register.tag
@basictag(takes_context=True)
def include_as_string(context, template_name):
    s = render_to_string(template_name, context)
    s = s.replace("'", "\\'")
    s = s.replace("\n", "\\\n")
    return "'%s'" % s


@register.tag
@blocktag
def attr(context, nodelist, attrname):
    """
    Sets an HTML attribute to a value if the value is not an empty string.
    """
    content = nodelist.render(context)

    if content.strip() == "":
        return ""

    return ' %s="%s"' % (attrname, content)


@register.filter
def escapespaces(value):
    """
    HTML-escapes all spaces with ``&nbsp;`` and newlines with ``<br />``.
    """
    return value.replace('  ', '&nbsp; ').replace('\n', '<br />')


@register.simple_tag
def ageid(timestamp):
    """
    Returns an ID based on the difference between a timestamp and the
    current time.

    The ID is returned based on the following differences in days:

      ========== ====
      Difference ID
      ========== ====
      0          age1
      1          age2
      2          age3
      3          age4
      4 or more  age5
      ========== ====
    """
    if timestamp is None:
        return ""

    # Convert datetime.date into datetime.datetime
    if timestamp.__class__ is not datetime.datetime:
        timestamp = datetime.datetime(timestamp.year, timestamp.month,
                                      timestamp.day)


    now = datetime.datetime.now()
    delta = now - (timestamp -
                   datetime.timedelta(0, 0, timestamp.microsecond))

    if delta.days == 0:
        return "age1"
    elif delta.days == 1:
        return "age2"
    elif delta.days == 2:
        return "age3"
    elif delta.days == 3:
        return "age4"
    else:
        return "age5"


@register.filter
def user_displayname(user):
    """
    Returns the display name of the user.

    If the user has a full name set, it will display this. Otherwise, it will
    display the username.
    """
    return user.get_full_name() or user.username


@register.filter
def humanize_list(value):
    """
    Humanizes a list of values, inserting commands and "and" where appropriate.

      ========================= ======================
      Example List              Resulting string
      ========================= ======================
      ``["a"]``                 ``"a"``
      ``["a", "b"]``            ``"a and b"``
      ``["a", "b", "c"]``       ``"a, b and c"``
      ``["a", "b", "c", "d"]``  ``"a, b, c, and d"``
      ========================= ======================
    """
    if len(value) == 0:
        return ""
    elif len(value) == 1:
        return value[0]

    s = ", ".join(value[:-1])

    if len(value) > 3:
        s += ","

    return "%s and %s" % (s, value[-1])


@register.filter
def contains(container, value):
    """
    Returns True if the specified value is in the specified container.
    """
    return value in container


@register.filter
def getitem(container, value):
    """
    Returns the attribute of a specified name from a container.
    """
    return container[value]


@register.filter
def exclude_item(container, item):
    """
    Excludes an item from a list.
    """
    if isinstance(container, list):
        container = list(container)

        if item in container:
            container.remove(item)
    else:
        raise TemplateSyntaxError, "remove_item expects a list"

    return container


@register.filter
def indent(value, numspaces=4):
    """
    Indents a string by the specified number of spaces.
    """
    indent_str = " " * numspaces
    return indent_str + value.replace("\n", "\n" + indent_str)


@register.filter
def basename(value):
    """
    Returns the basename of a path.
    """
    return os.path.basename(value)


@register.filter(name="range")
def range_filter(value):
    """
    Turns an integer into a range of numbers.

    This is useful for iterating with the "for" tag. For example:

    {% for i in 10|range %}
      {{i}}
    {% endfor %}
    """
    return range(value)


@register.filter
def realname(user):
    """
    Returns the real name of a user, if available, or the username.

    If the user has a full name set, this will return the full name.
    Otherwise, this returns the username.
    """
    full_name = user.get_full_name()
    if full_name == '':
        return user.username
    else:
        return full_name


@register.filter
@stringfilter
def paragraphs(text):
    """
    Adds <p>...</p> tags around blocks of text in a string. This expects
    that each paragraph in the string will be on its own line. Blank lines
    are filtered out.
    """
    s = ""

    for line in text.splitlines():
        if line:
            s += "<p>%s</p>\n" %  line

    return mark_safe(s)
paragraphs.is_safe = True
