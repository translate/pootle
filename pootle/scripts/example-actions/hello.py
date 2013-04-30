#
# Example "hello, world" extension action
#

from pootle.scripts.actions import *

class HelloAction(ProjectAction):
    """
    Say hello to the user (in their own language)
    """

    def run(self, **kwargs):
        super(type(self), self).run(**kwargs)
        self.showoutput("Hello, world!")

hello = HelloAction(category="Other actions", title="Say hello")
