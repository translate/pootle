
from feeds import NoticeFeeds
from django.conf.urls.defaults import *
from pootle_notifications.views import *

urlpatterns = patterns('',
    (r'^notice/viewitem/(?P<notice_id>[^/]*)/$', view_notice_item),
    (r'^(?P<url>.*)/rss.xml/$', NoticeFeeds),
    (r'^(?P<language_code>[^/]*)/notices/$', lang_notices),
    (r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/notices/$', transproj_notices),
)
