import requests
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from login.utils import decrypt_token

# GitHub Actions 실행 결과 확인
class GitHubActionsStatus(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        repo_name = request.query_params.get("repo_name")
        branch = request.query_params.get("branch", "main")

        if not repo_name:
            return Response({
                "error": "Missing required parameter: repo_name"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            access_token = decrypt_token(user.github_access_token)
        except Exception as e:
            return Response({
                "error": "Token decrypt failed",
                "detail": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        github_username = user.username
        api_url = f"https://api.github.com/repos/{github_username}/{repo_name}/actions/runs?branch={branch}&per_page=1"

        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github+json"
        }

        res = requests.get(api_url, headers=headers)

        try:
            result_data = res.json()
        except ValueError:
            return Response({
                "error": "Invalid JSON from GitHub",
                "raw_response": res.text
            }, status=status.HTTP_502_BAD_GATEWAY)

        if res.status_code != 200:
            return Response({
                "error": "GitHub API error",
                "status_code": res.status_code,
                "detail": result_data
            }, status=res.status_code)

        runs = result_data.get("workflow_runs", [])
        if not runs:
            return Response({
                "message": f"No workflow runs found on branch '{branch}'"
            }, status=status.HTTP_204_NO_CONTENT)

        latest = runs[0]
        return Response({
            "id": latest["id"],
            "name": latest.get("name"),
            "branch": latest.get("head_branch"),
            "status": latest.get("status"),
            "conclusion": latest.get("conclusion"),
            "html_url": latest.get("html_url"),
            "updated_at": latest.get("updated_at")
        }, status=status.HTTP_200_OK)