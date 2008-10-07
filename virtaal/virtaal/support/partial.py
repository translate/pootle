#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of Virtaal.
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

__all__ = ['partial', 'compose', 'post']


def copy_attrs(source_func, target_func):
    for attr in ('__module__', '__name__', '__doc__'):
        setattr(target_func, attr, getattr(source_func, attr))
    for attr in ('__dict__',):
        getattr(target_func, attr).update(getattr(source_func, attr, {}))

def partial(f, *args, **kwargs):
    """Given a function foo, return a new function bar with some parameters already specified.

    This can best be illustrated by an example:

    >>> def foo(a, b):
    ...    return a - b
    ...
    ... bar = partial(foo, b=2)
    ... bar(1)
    -1

    Partial application is more powerful than Python lambda functions, since the latter
    does not store a copy to its environment; thus if you reference a variable i in a
    lambda and i changes, then the lambda will also see a changed copy.
    """
    def new_f(*new_args, **new_kwargs):
        all_args = args + new_args
        kwargs.update(new_kwargs)
        return f(*all_args, **kwargs)

    copy_attrs(f, new_f)
    return new_f

def compose(*funcs):
    """Compose two or more functions into a single function.

    This operates as mathematical composition. Thus, C{compose(a, b, c)}
    is equivalent to M{a . b . c} in mathematical notation. In Python,
    this can also be written as C{lambda *args: a(b(c(*args)))}.
    """
    def new_f(args):
        return reduce(lambda args, f: f(args), reversed(funcs), args)

    # If we compose a, b and c, we make the name of the composed function
    # "a.b.c"
    setattr(new_f, '__name__', ".".join(f.__name__ for f in funcs))
    # Create a module name of the form a.__module__:b.__module__:c.__module__
    # TODO: Check whether such a module name will cause trouble
    setattr(new_f, '__module__', ":".join(f.__module__ for f in funcs))
    setattr(new_f, '__doc__', "composition")

    return new_f

def post(post_f):
    """Turn a normal Python function into a decorator which causes the code in
    the function to be executed after the code in the decorated function is
    executed.

    For example, suppose that you have a function foo. If you want the code in
    bar to be executed after the code in foo, you can decorate foo as follows::

        @post(bar)
        def foo(a, b, c, ...)

    The function bar needs to have a signature as follows::
        def bar(foo_return_value, a, b, c, ...)

    Thus, the first parameter of bar is the return value of foo and the rest of
    its parameters are identical to that of foo (this is so that bar has access to
    the parameters.

    As a concrete example, an implementation of bar might look something like::
        def bar(foo_return, a, *args):
            print 'The return value of the function that ran before me is %s' % repr(foo_return)
            print 'The first parameter is %s'% repr(a)

            return foo_return + 42

    and the definition of foo something like::
        @post(bar)
        def foo(a, b, c):
            print 'I am foo'
            return 0

    Thus::
        >>> foo(1, 2, 3)
        ... I am foo
        ... The return value of the function that ran before me is 0
        ... The first parameter is 1
        ... 42
    """
    def decorator(f):
        def new_f(*args, **kwargs):
            return post_f(f(*args, **kwargs), *args, **kwargs)

        copy_attrs(f, new_f)
        setattr(new_f, '__name__', f.__name__ + "+" + post_f.__name__)
        setattr(new_f, '__module__', f.__module__ + "+" + post_f.__module__)
        return new_f

    copy_attrs(post_f, decorator)
    return decorator
