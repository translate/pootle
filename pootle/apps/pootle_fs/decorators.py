
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import functools


def emits_state(pre=None, post=None):

    def class_wrapper(f):

        @functools.wraps(f)
        def method_wrapper(self, state, response, **kwargs):
            if pre:
                pre.send(
                    self.__class__,
                    plugin=self,
                    state=state,
                    response=response)
            result = f(self, state, response, **kwargs)
            if post:
                post.send(
                    self.__class__,
                    plugin=self,
                    state=state,
                    response=response)
            return result
        return method_wrapper
    return class_wrapper


def responds_to_state(f):

    @functools.wraps(f)
    def method_wrapper(self, *args, **kwargs):
        if args:
            state = args[0]
        elif "state" in kwargs:
            state = kwargs["state"]
            del kwargs["state"]
        else:
            state = self.state(
                pootle_path=kwargs.get("pootle_path"),
                fs_path=kwargs.get("fs_path"))
        if len(args) > 1:
            response = args[1]
        elif "response" in kwargs:
            response = kwargs["response"]
            del kwargs["response"]
        else:
            response = self.response(state)

        return f(self, state, response, **kwargs)
    return method_wrapper
