#!/usr/bin/env python

"""tests decoration handling functions that are used by checks"""

from translate.filters import decoration

def test_find_marked_variables():
    """check that we cna identify variables correctly, first value is start location, i
    second is avtual variable sans decoations"""
    variables = decoration.findmarkedvariables("The <variable> string", "<", ">")
    assert variables == [(4, "variable")]
    variables = decoration.findmarkedvariables("The $variable string", "$", 1)
    assert variables == [(4, "v")]
    variables = decoration.findmarkedvariables("The $variable string", "$", None)
    assert variables == [(4, "variable")]
    variables = decoration.findmarkedvariables("The $variable string", "$", 0)
    assert variables == [(4, "")]
    variables = decoration.findmarkedvariables("The &variable; string", "&", ";")
    assert variables == [(4, "variable")]
    variables = decoration.findmarkedvariables("The &variable.variable; string", "&", ";")
    assert variables == [(4, "variable.variable")]

