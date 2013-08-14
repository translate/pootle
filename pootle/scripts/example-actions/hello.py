#!/usr/bin/env python
""" Example "hello, world" extension action """

import os

from pootle.scripts.actions import TranslationProjectAction, StoreAction


class HelloAction(TranslationProjectAction, StoreAction):
    """_
    Say hello to the user (in their own language)
    """

    def __init__(self, **kwargs):
        super(HelloAction, self).__init__(**kwargs)
        self.icon = 'icon-external-link'

    def run(self, path, root, tpdir,  # pylint: disable=R0913
            language, project, store='*', style='', **kwargs):
        """Say hello when the user clicks the link"""
        filepath = os.path.join(root, tpdir, store)
        self.set_output(''.join(["Hello, world! "
                                 "My name is '%s'. " % self.title,
                                 "My project code is '%s'. " % project,
                                 "My language code is '%s'. " % language,
                                 "My store is '%s'. " % store,
                                 "My URL path is '%s'. " % path,
                                 "My file path is '%s'. " % filepath,
                                 "My project style is '%s'. " % style,
                                 ]))
        self.set_error("'hello' extension action is not yet localized")

HelloAction.hello = HelloAction(category="Other actions", title="Say hello")
