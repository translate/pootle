#!/usr/bin/env python
""" Extension action to generate Mozilla language tar archives"""

from pootle.scripts.actions import DownloadAction, TranslationProjectAction

from translate.convert import po2moz


class MozillaTarballAction(DownloadAction, TranslationProjectAction):
    """Download Mozilla language properties tarball"""

    def run(self, project, language, **kwargs):
        """Generate a Mozilla language properties tarball"""
        super(MozillaTarballAction, self).run(**kwargs)
	# TODO: redirect progress output to string, add JS output autorefresh
        # (requires background subprocess - or use celery???)
        po2moz.main('-t', 'templates-en-US', language + "-po", language)


MozillaTarballAction.moztar = MozillaTarballAction(category="Other actions",
                                                   title="Download tarball")
