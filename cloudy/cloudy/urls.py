from django.contrib import admin
from django.urls import path
from login.views import GitHubLogin, GitHubOAuthURLView, Logout, ProfileView
from github.views.repo import GitHubRepoList, GitHubCreateRepo, GitHubRepoFileContentsView
from github.views.upload import GitHubUploadFiles
from github.views.secrets import GitHubUploadSecrets
from github.views.github_actions import GitHubActionsStatus
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
    path('github/repo-files/', GitHubRepoFileContentsView.as_view()),
    path('github/upload-files/', GitHubUploadFiles.as_view()),
    path('github/secrets/', GitHubUploadSecrets.as_view()),
    path('github/actions-status/', GitHubActionsStatus.as_view()),
]