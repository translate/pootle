#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of Spelt.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

from lxml import objectify

from spelt.common import exceptions, _

from spelt.models.id_manager import IDManager

class XMLModel(IDManager):
    """
    This base-class of that provides common XML reading and writing methods.

    This class is only meant to be inherited from, but can conceivably be used
    on its own (see test_xml_model).
    """

    # CONSTRUCTORS #
    def __init__(self, tag, values, attribs, elem=None):
        """Constructor.

            @type  tag:     str
            @param tag:     The XML-tag to use to represent an instance of this model
            @type  values:  list
            @param values:  A list of names of accepted the child values
            @type  attribs: list
            @param attribs: A list of accepted attributes
            @type  elem:    lxml.objectify.ObjectifiedElement
            @param elem:    The XML element wrapped by the model
            """
        assert isinstance(tag, str) and len(tag) > 0

        # Bypass XMLModel.__setattr__()
        super_set = super(XMLModel, self).__setattr__
        super_set('tag', tag)
        super_set('values', values)
        super_set('attribs', attribs)

        if elem is None:
            super_set('elem', objectify.Element(tag))
        else:
            super_set('elem', elem)

        super(XMLModel, self).__init__()

    # METHODS #
    def validate_data(self):
        """
        Checks whether all data-constraints are met.

        A successful validation should mean that:
            * All required data is present
            * All required data members are of the correct type

        Notes to this function's relevance in XML-related operations:
            - Optional values (not attributes) may be None.
            - Attributes declared in XMLModel.__init__ must have a non-None
              value.

        This method is empty and should be overridden in inheriting classes.
        It should throw an exception if validation fails.
        """
        pass

    # SPECIAL METHODS #
    def __getattribute__(self, name):
        super_getattr = super(XMLModel, self).__getattribute__
        elem = super_getattr('elem')

        if name in super_getattr('attribs'):
            if name == 'id' or name.endswith('_id'):
                # Automatically convert ID's to int()s
                return int(elem.attrib[name])
            else:
                return elem.attrib[name]
        elif name in super_getattr('values'):
            return unicode(getattr(elem, name))

        return super_getattr(name)

    def __setattr__(self, name, value):
        if name in ('attribs', 'values'):
            super(XMLModel, self).__setattr__(name, value)
        elif name in self.attribs:
            # Give the 'id' attribute special treatment, because we love it so much. :/
            if name == 'id':
                self._set_id(value)
                self.elem.set('id', str(self._id))
                return
            self.elem.set(name, str(value))
        elif name in self.values:
            setattr(self.elem, name, value)

        super(XMLModel, self).__setattr__(name, value)

    def __repr__(self):
        return str(self)

    def __str__(self):
        #return '<%s[%s][%s]>' % (
        #    self.__class__.__name__,
        #    ','.join([( '@%s="%s"' % (a, str(getattr(self, a))) ) for a in self.attribs]),
        #    # Choose one of the two lines below, but not both. The first line
        #    # produces less verbose results than the second...
        #    #','.join([v for v in self.values])
        #    ','.join([( '%s="%s"' % (v, repr(getattr(self, v))) ) for v in self.values])
        #)
        return '<%s(id=%d)[%s]>' % (
            self.__class__.__name__, self.id,
            ','.join([( '%s="%s"' % (v, repr(getattr(self, v))) ) for v in self.values])
        )
