from django.urls import path

from plans.api.goals import goals
from plans.api.tasks import tasks_manage
from plans.api.plan_doc import plan_doc
from plans.api.adjust import adjust


urlpatterns = [
    path('plan/goals', goals),
    path('plan/tasks', tasks_manage),
    path('plan/doc', plan_doc),
    path('plan/adjust', adjust),
]

