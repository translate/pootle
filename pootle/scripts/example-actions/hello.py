#!/usr/bin/env python
""" Example "hello, world" extension action """

from pootle.scripts.actions import TranslationProjectAction, StoreAction


class HelloAction(TranslationProjectAction, StoreAction):
    """
    Say hello to the user (in their own language)
    """

    def run(self, project, language, store, **kwargs):
        """Say hello when the user clicks the link"""
        super(HelloAction, self).run(**kwargs)
        self.set_output("Hello, world! "
                        "My project is '" + project + "'. "
                        "My language is '" + language + "'. "
                        "My store is '" + store + "'. ")

HelloAction.hello = HelloAction(category="Other actions", title="Say hello")
