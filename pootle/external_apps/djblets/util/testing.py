#
# djblets/util/testing.py - Some classes useful for unit testing django-based
#                           applications
#
# Copyright (c) 2007  David Trowbridge
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
#

from django.template import Node
from django.test import TestCase


class StubNodeList(Node):
    def __init__(self, default_text):
        self.default_text = default_text

    def render(self, context):
        return self.default_text


class StubParser:
    def __init__(self, default_text):
        self.default_text = default_text

    def parse(self, until):
        return StubNodeList(self.default_text)

    def delete_first_token(self):
        pass


class TagTest(TestCase):
    """Base testing setup for custom template tags"""

    def setUp(self):
        self.parser = StubParser(self.getContentText())

    def getContentText(self):
        return "content"
