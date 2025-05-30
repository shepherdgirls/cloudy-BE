"""
URL configuration for cloudy project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from login.views import GitHubLogin, GitHubOAuthURLView, Logout, ProfileView
from github.views.repo import GitHubRepoList, GitHubCreateRepo
from github.views.upload import GitHubUploadFiles
from github.views.secrets import GitHubUploadSecrets
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cloudy-auth/github/', GitHubLogin.as_view(), name='github-login'),
    path('cloudy-auth/github-login/', GitHubOAuthURLView.as_view()),
    path('cloudy/logout', Logout.as_view()),
    path('cloudy/cherry', ProfileView.as_view()),
    path("cloudy/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('github/repos/', GitHubRepoList.as_view()),
    path('github/create-repo/', GitHubCreateRepo.as_view()),
    path('github/upload-files/', GitHubUploadFiles.as_view()),
    path('github/secrets/', GitHubUploadSecrets.as_view()),
]