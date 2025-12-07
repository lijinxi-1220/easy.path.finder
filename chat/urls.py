from django.urls import path

from chat.api.interact import interact
from chat.api.guide import resume_guide
from chat.api.history import history
from chat.api.messages import messages


urlpatterns = [
    path('chat/interact', interact),
    path('chat/resume_guide', resume_guide),
    path('chat/history', history),
    path('chat/messages', messages),
]
