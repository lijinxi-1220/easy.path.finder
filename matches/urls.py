from django.urls import path

from matches.api.job_profile import job_profile, job_detail
from matches.api.school_detail import school_detail
from matches.api.match_analysis import match_analysis
from matches.api.recommend import recommend
from matches.api.admin import import_job_profiles, import_schools


urlpatterns = [
    path('match/job_profile', job_profile),
    path('match/job_detail', job_detail),
    path('match/school_detail', school_detail),
    path('match/analysis', match_analysis),
    path('match/recommend', recommend),
    path('match/admin/job_profiles/import', import_job_profiles),
    path('match/admin/schools/import', import_schools),
]
