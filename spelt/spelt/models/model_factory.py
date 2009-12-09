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

from spelt.common              import *
from spelt.models.pos          import PartOfSpeech
from spelt.models.root         import Root
from spelt.models.source       import Source
from spelt.models.surface_form import SurfaceForm
from spelt.models.user         import User

class ModelFactory(object):
    """
    Factory class that creates models from XML elements.
    """

    # CLASS MEMBERS #
    model_name_map = {
        'part_of_speech' : PartOfSpeech,
        'root'           : Root,
        'source'         : Source,
        'surface_form'   : SurfaceForm,
        'user'           : User
    }

    # STATIC METHODS #
    @staticmethod
    def create_model_from_elem(elem):
        """Create an appropriate model from the given XML element.
            @type  elem: lxml.objectify.ObjectifiedElement
            @param elem: The XML element to create a model from.
            """
        if not ModelFactory.model_name_map.has_key(elem.tag):
            raise InvalidElementError(_('Invalid XML element with tag "%s"') % (elem.tag))

        klass = ModelFactory.model_name_map[elem.tag]
        return klass(elem=elem)
