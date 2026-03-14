"""
URL configuration for stem_dukich_web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.views.static import serve # Thêm dòng này
from django.urls import re_path # Thêm dòng này
from django.contrib import admin
from django.urls import path, include
from judge import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API & Tools
    path('api/get-task/', views.get_task),
    path('api/update-result/<int:sub_id>/', views.update_result, name='update_result'),
    path('api/user-ui/focus-mode/', views.toggle_focus, name="toggle_focus"),
    path('markdownx/', include('markdownx.urls')),

    # Problems & Submissions (Thêm / vào cuối hết cho tôi)
    path('problems/', views.problems, name="problems_list"),
    path('problem/<str:problem_code>/', views.problem),
    path('problem/<str:problem_code>/printed_view/', views.problem_print),
    path('submit/<str:problem_code>/', views.submit_code),
    path('submissions/', views.submissions),
    path('submissions/<int:id>/', views.submission),

    # Profile
    path('profile/update/', views.profile_update, name='profile-update'),
    path('profile/delete/', views.user_delete, name='user-delete'),
    path('profile/change-password/', views.change_password, name='password_change'),
    path('profile/<str:username>/', views.profile),

    # Contests (Khu vực nhạy cảm, cần chính xác tuyệt đối)
    path('contests/', views.contests),
    path('contest/<int:contest_id>/', views.contest_detail, name="contest_detail"),
    path('register-contest/<int:contest_id>/', views.register_contest),
    path('contest/<int:contest_id>/rankings/', views.contest_leaderboard),
    path('contest/<int:contest_id>/submit/<str:problem_code>/', views.submit_code_contest),

    # Rankings chung
    path('rankings/', views.ranks),
    path('', views.home_view),
]
if not settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]