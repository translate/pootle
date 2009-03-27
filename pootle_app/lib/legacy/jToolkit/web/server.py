#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Receives requests from the clients via Apache and responds with html strings
   Typically, the response will include html that represents a toolbar, a form and a grid
   May also (later) include pop up windows and error messages.
"""      

# Copyright 2002, 2003 St James Software
# 
# This file is part of jToolkit.
#
# jToolkit is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# jToolkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with jToolkit; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

class Redirect:
  """an object that instructs the server to redirect the client to another page..."""
  def __init__(self, location, ispermanent=False, withpage=False, withtemplate=False):
    """location is the new URL. ispermanent is the type of redirect
    withpage is a widgets Page to use for the redirect, if desired
    withtemplate is a tuple of (templatename, templatevars) to be used with TemplateServer)"""
    self.location = location
    self.ispermanent = ispermanent
    self.withpage = withpage
    self.withtemplate = withtemplate

