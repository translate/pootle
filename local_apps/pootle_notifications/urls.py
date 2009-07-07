
from feeds import NoticeFeeds
from django.conf.urls.defaults import *
from pootle_notifications.views import *

urlpatterns = patterns('',
    (r'^(?P<language_code>[^/]*)/notices/$', view_lang_notices),
    (r'^notice/viewitem/(?P<notice_id>[^/]*)/$', view_notice_item),
    (r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/notices/$', view_transproj_notices),
    (r'^(?P<url>.*)/rss.xml/$', NoticeFeeds),
    (r'^notice/(?P<language_code>[^/]*)/$', lang_notice),
    (r'^notice/(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/$', transproj_notice),
    (r'^notice/(?P<project_code>[^/]*)/$', proj_notice),
)
