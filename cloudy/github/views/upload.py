import requests
import base64
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from login.utils import decrypt_token

class GitHubUploadFiles(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data

        try:
            access_token = decrypt_token(user.github_access_token)
        except Exception as e:
            return Response({"error": "Token decrypt failed", "detail": str(e)},
                            status=status.HTTP_400_BAD_REQUEST)

        owner = user.username
        repo = data.get("repo_name")
        branch = data.get("branch") 
        commit_message = data.get("commit_message")
        files = data.get("files", [])

        if not all([repo, branch, commit_message, files]):
            return Response({"error": "Missing required fields"},
                            status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github+json",
        }

        # 1. 브랜치 존재 여부 확인
        ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch}"
        ref_resp = requests.get(ref_url, headers=headers)

        if ref_resp.status_code != 200:
            return Response({
                "error": f"Branch '{branch}' does not exist. Please create it first."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 2. 파일 업로드
        for file in files:
            path = file.get("path")
            content = file.get("content")
            if not path or content is None:
                return Response({
                    "error": "Each file must include 'path' and 'content'"
                }, status=status.HTTP_400_BAD_REQUEST)

            encoded = base64.b64encode(content.encode()).decode()
            file_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
            file_payload = {
                "message": commit_message,
                "content": encoded,
                "branch": branch
            }

            upload_resp = requests.put(file_url, headers=headers, json=file_payload)

            if upload_resp.status_code not in (200, 201):
                return Response({
                    "error": f"Failed to upload '{path}'",
                    "detail": upload_resp.json()
                }, status=upload_resp.status_code)

        return Response({
            "message": f"Files uploaded successfully"
        }, status=status.HTTP_201_CREATED)
