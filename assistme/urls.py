from django.urls import include, path
from rest_framework import routers
from assistme import views


router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'transcripts', views.TranscriptViewSet)


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),

    path('document/', views.document),
    path('requesttexttospeach/', views.request_text_to_speach),
    path('webex/', views.webex_meetings),
    path('webex/<int:pk>/', views.webex_meeting_detail),
    path('command/', views.do_command),
]



urlpatterns += router.urls