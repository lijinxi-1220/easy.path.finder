# users/urls.py
from django.urls import path

from users.views import index
from users.api.register import register
from users.api.login import login
from users.api.code import login_code, send_code
from users.api.profile import profile
from users.api.logout import logout


urlpatterns = [
    path('', index),
    path('register', register),
    path('login', login),
    path('login/code', login_code),
    path('send_code', send_code),
    path('profile/<str:user_id>', profile),
    path('logout', logout),
]
