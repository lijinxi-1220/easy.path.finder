from django.urls import path

from userdata.api.privacy import privacy
from userdata.api.history import history
from userdata.api.progress import progress


urlpatterns = [
    path('user/privacy', privacy),
    path('user/history', history),
    path('user/progress', progress),
]

