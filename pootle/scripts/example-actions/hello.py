#!/usr/bin/env python
""" Example "hello, world" extension action """

from pootle.scripts.actions import ProjectAction


class HelloAction(ProjectAction):
    """
    Say hello to the user (in their own language)
    """

    def run(self, **kwargs):
        """Say hello when the user clicks the link"""
        super(HelloAction, self).run(**kwargs)
        self.showoutput("Hello, world!")

HelloAction.hello = HelloAction(category="Other actions", title="Say hello")
