from django.urls import include, path
from rest_framework import routers

from state import views

router = routers.DefaultRouter()

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    path('command/', views.get_command),
    path('client/', views.get_query),

]

urlpatterns += router.urls