
from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
from pootle_notifications.models import LanguageNotice
from pootle_app.models import Language
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
        content = LanguageNotice(content_object = lang)
        return content

    def items(self, obj):
        return LanguageNotice.objects.get_notices(obj.object_id, obj.content_type_id)

    def item_link(self, obj):
        return "/noticelink/"
