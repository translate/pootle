#!/usr/bin/env python
""" Example "hello, world" extension action """

from pootle.scripts.actions import TranslationProjectAction, StoreAction


class HelloAction(TranslationProjectAction, StoreAction):
    """_
    Say hello to the user (in their own language)
    """

    def __init__(self, **kwargs):
        super(HelloAction, self).__init__(**kwargs)
        self.icon = 'icon-external-link'

    def run(self, root, tpdir, language, project,  # pylint: disable=R0913
            store='*', style='', **kwargs):
        """Say hello when the user clicks the link"""
        self.set_output(''.join(["Hello, world! "
                                 "My project code is '%s'. " % project,
                                 "My language code is '%s'. " % language,
                                 "My store is '%s'. " % store,
                                 "My path is '%s'. " % '|'.join([root, tpdir,
                                                                 store]),
                                 "My project style is '%s'. " % style,
                                 ]))
        self.set_error("'hello' extension action is not yet localized")

HelloAction.hello = HelloAction(category="Other actions", title="Say hello")
