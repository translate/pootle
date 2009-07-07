
from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
from pootle_notifications.models import Notice
from pootle_app.models import Language, Project, TranslationProject
from django.core.exceptions import ObjectDoesNotExist

class LanguageFeeds(Feed):
    """
    Hard-coded link, description and title as this is a test app.
    """
    link = "/feeds/"
    description = "Feeds for language notices"
    title = "Language Feeds"
    
    def get_object(self, bits):

        """
        Get object_id and content_type_id based on bits
        """
        lang = Language.objects.get(code=bits[0])
        content = Notice(content_object = lang)
        return content

    def items(self, obj):
        return Notice.objects.get_notices(obj)

    def item_link(self, obj):
        return "/noticelink/"

class ProjectFeeds(Feed):
    """
    Hard-coded link, description and title as this is a test app.
    """
    link = "/feeds/"
    description = "Feeds for project notices"
    title = "Project Feeds"
    
    def get_object(self, bits):

        """
        Get object_id and content_type_id based on bits
        """
        proj = Project.objects.get(code=bits[0])
        content = Notice(content_object = proj)
        return content

    def items(self, obj):
        return Notice.objects.get_notices(obj)

    def item_link(self, obj):
        return "/noticelink/"

class TransProjectFeeds(Feed):
    """
    Hard-coded link, description and title as this is a test app.
    """
    link = "/feeds/"
    description = "Feeds for translation project  notices"
    title = "Translation project Feeds"
    
    def get_object(self, bits):

        """
        Get object_id and content_type_id based on bits
        """
        real_path = bits[0] + "/" + bits[1]
        trans_proj = TranslationProject.objects.get(real_path=real_path)
        content = Notice(content_object = trans_proj)
        return content

    def items(self, obj):
        return Notice.objects.get_notices(obj)

    def item_link(self, obj):
        return "/noticelink/"
