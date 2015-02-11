from django.conf.urls import patterns, include, url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),

    # For the registration module
    # TODO: AllAuth
    #url(r'^accounts/', include('registration.urls')),
    #url(r'^accounts/', views.index),

    # For viewing and changing user information
    url(r'^answers/(?P<user>[^/]+)/(?P<course>[^/]+)/(?P<exercise>[^/]+)',
        views.show_answers, name='show_answers'),
    url(r'^user/(?P<user_name>[^/]+)/$', views.user),
    url(r'^profile/$', views.user_profile),
    url(r'^profile/save/$', views.user_profile_save),

    # For calendar POST requests
    url(r'^calendar/(?P<calendar_id>\d+)/(?P<event_id>\d+)/$', views.calendar_post),

    # Sandbox: admin view & answer for content pages without saved results
    url(r'^sandbox/(?P<content_slug>[^/]+)/$', views.content, {'sandbox': True,}, name='sandbox',),

    # Help pages
    url(r'^help/$', views.help_list, name='help_list',),
    url(r'^help/markup/$', views.markup_help, name='markup_help',),

    # Course front page and content views
    url(r'^(?P<course_slug>[^/]+)/$', views.course, name='course'),
    url(r'^(?P<course_slug>[^/]+)/(?P<content_slug>[^/]+)/$', views.content, name='content'),

    # Exercise sending for checking, progress and evaluation views
    url(r'^(?P<course_slug>[^/]+)/(?P<content_slug>[^/]+)/check/$', views.check_answer, name='check'),
    url(r'^(?P<course_slug>[^/]+)/(?P<content_slug>[^/]+)/progress/(?P<task_id>[^/]+)/$',
        views.check_progress, name='check_progress'),
    url(r'^(?P<course_slug>[^/]+)/(?P<content_slug>[^/]+)/evaluation/(?P<task_id>[^/]+)/$',
        views.file_exercise_evaluation, name='file_exercise_evaluation'),
]

# For serving uploaded files on development server only:
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
