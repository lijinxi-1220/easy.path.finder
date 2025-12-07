from django.urls import path

from services.api.recommend import recommend
from services.api.mentors import mentors
from services.api.consult import consult
from services.api.projects import projects
from services.api.subscription import subscription
from services.api.subscription_webhook import subscription_webhook


urlpatterns = [
    path('service/recommend', recommend),
    path('service/mentors', mentors),
    path('service/consult', consult),
    path('service/projects', projects),
    path('service/subscription', subscription),
    path('service/subscription/webhook', subscription_webhook),
]
