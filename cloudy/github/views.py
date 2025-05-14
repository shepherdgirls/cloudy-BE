import requests
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from login.utils import decrypt_token

# repo 조회
class GitHubRepoList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            access_token = decrypt_token(user.github_access_token)
        except Exception as e:
            return Response({"error": "Token decrypt failed", "detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        github_api_url = "https://api.github.com/user/repos?per_page=100&visibility=public"

        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github+json",
        }

        res = requests.get(github_api_url, headers=headers)

        try:
            repos_data = res.json()
        except ValueError:
            return Response({
                "error": "Invalid JSON from GitHub",
                "raw_response": res.text
            }, status=status.HTTP_502_BAD_GATEWAY)

        if res.status_code != status.HTTP_200_OK:
            return Response({
                "error": "GitHub API error",
                "status_code": res.status_code,
                "detail": res.json()
            }, status=res.status_code)
        
        repos_data = res.json()
        response_data = []

        for repo in repos_data:
            response_data.append({
                "name": repo["name"],
                "full_name": repo["full_name"],
                "html_url": repo["html_url"],
                "default_branch": repo["default_branch"],
                "owner": repo["owner"]["login"],
            })

        return Response(response_data, status=status.HTTP_200_OK)