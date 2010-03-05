#
# djblets_images.py -- Image-related template tags
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


import os

try:
    from PIL import Image
except ImportError:
    import Image

from django import template
from django.conf import settings


register = template.Library()


@register.simple_tag
def crop_image(file, x, y, width, height):
    """
    Crops an image at the specified coordinates and dimensions, returning the
    resulting URL of the cropped image.
    """
    filename = file.name

    if filename.find(".") != -1:
        basename, format = filename.rsplit('.', 1)
        new_name = '%s_%s_%s_%s_%s.%s' % (basename, x, y, width, height, format)
    else:
        basename = filename
        new_name = '%s_%s_%s_%s_%s' % (basename, x, y, width, height)

    new_path = os.path.join(settings.MEDIA_ROOT, new_name)
    new_url = os.path.join(settings.MEDIA_URL, new_name)

    if not os.path.exists(new_path):
        try:
            image = Image.open(os.path.join(settings.MEDIA_ROOT, filename))
            image = image.crop((x, y, x + width, y + height))
            image.save(new_path, image.format)
        except (IOError, KeyError):
            return ""

    return new_url


# From http://www.djangosnippets.org/snippets/192
@register.filter
def thumbnail(file, size='400x100'):
    """
    Creates a thumbnail of an image with the specified size, returning
    the URL of the thumbnail.
    """
    x, y = [int(x) for x in size.split('x')]

    filename = file.name
    if filename.find(".") != -1:
        basename, format = filename.rsplit('.', 1)
        miniature = '%s_%s.%s' % (basename, size, format)
    else:
        basename = filename
        miniature = '%s_%s' % (basename, size)

    miniature_filename = os.path.join(settings.MEDIA_ROOT, miniature)
    miniature_url = os.path.join(settings.MEDIA_URL, miniature)

    if not os.path.exists(miniature_filename):
        try:
            image = Image.open(os.path.join(settings.MEDIA_ROOT, filename))
            image.thumbnail([x, y], Image.ANTIALIAS)
            image.save(miniature_filename, image.format)
        except IOError:
            return ""
        except KeyError:
            return ""

    return miniature_url
