from django.urls import path

from resumes.api.upload import upload_parse
from resumes.api.score import score
from resumes.api.optimize import optimize
from resumes.api.manage import manage
from resumes.api.export import export


urlpatterns = [
    path('resume/upload', upload_parse),
    path('resume/score', score),
    path('resume/optimize', optimize),
    path('resume/manage', manage),
    path('resume/export', export),
]

