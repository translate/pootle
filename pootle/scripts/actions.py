#!/usr/bin/env python

import logging

class ExtensionAction(object):
    """
    This is an (abstract) base class for all extension actions, creating one
    would not actually register any actions in the menu system - it exists
    just to provide a place for any common code
    """

    def __init__(self, category, title):
        self._category = category
        self._title = title

    def __repr__(self):
        """
        >>> print ExtensionAction('cat', 'dog')
        ExtensionAction("cat", "dog")
        >>> print ProjectAction(title="dog", category="cat")
        ProjectAction(category="cat", title="dog")
        """
        if type(self) is ExtensionAction:
            return (type(self).__name__ + '("' + self.category + '", "' +
            self.title + '")')
        else:
            return (type(self).__name__ + '(category="' + self.category +
                    '", title="' + self.title + '")')

    @property
    def category(self):
        """
        The (unlocalized) text of the category in which the action will be
        placed.  An example might be "Translate offline" if the action would
        be placed together with the "Download (.zip)" and "Upload" actions.
        """
        return self._category

    @property
    def title(self):
        """The (unlocalized) text for the action link."""
        return self._title

    def run(self, project='*', language='*', store='*'):
        """Run an extension action: this base class implementation just logs"""
        logging.warning("running %s %s for project %s language %s store %s",
                        type(self), self.title, project, language, store)

    def showoutput(self, stream):
        """Display results of action in the current page"""
        # display output on the current page

    def newpage(self, stream):
        """Display results of action on a results page"""
        # display output on a new results page

    def returnfile(self, stream):
        """Display link to a file containing results"""
        # display link to results file

class ProjectAction(ExtensionAction):
    """
    This is an extension action that operates on a project (across all
    languages).
    """

    def __init__(self, **kwargs):
        """
        >>> print ProjectAction(category="cat", title="dog")
        ProjectAction(category="cat", title="dog")
        """
        ExtensionAction.__init__(self, kwargs['category'], kwargs['title'])

        # register action on project page
        # register action on language page
        # register action on translationproject page
        # register action on store page

class LanguageAction(ExtensionAction):
    """
    This is an extension action that operates on a language (across all
    projects).
    """

    def __init__(self, **kwargs):
        """
        >>> print LanguageAction(category="cat", title="dog")
        LanguageAction(category="cat", title="dog")
        """
        ExtensionAction.__init__(self, kwargs['category'], kwargs['title'])

        # register action on language page
        # register action on translationproject page
        # register action on store page

class TranslationProjectAction(ExtensionAction):
    """
    This is an extension action that operates on a particular translation of
    a project for a particular language.
    """

    def __init__(self, **kwargs):
        """
        >>> print TranslationProjectAction(category="cat", title="dog")
        TranslationProjectAction(category="cat", title="dog")
        """
        ExtensionAction.__init__(self, kwargs['category'], kwargs['title'])

        # register action on translationproject page
        # register action on store page

class StoreAction(ExtensionAction):
    """
    This is an extension action that operates on a particular store (translation
    file) of a particular language for a particular project.
    """

    def __init__(self, **kwargs):
        """
        >>> print StoreAction(category="cat", title="dog")
        StoreAction(category="cat", title="dog")
        """
        ExtensionAction.__init__(self, kwargs['category'], kwargs['title'])

        # register action on store page

class CommandAction(object):
    """
    This is a class for extension actions that can be invoked from the command
    line; it is intended to be used as a mixin for other extension actions;
    since you can always write an standalone script for a command action that
    is not available within the Pootle UI.
    """

    def __init__(self):
        pass
        # register action as management command

if __name__ == "__main__":
    import doctest
    doctest.testmod()
