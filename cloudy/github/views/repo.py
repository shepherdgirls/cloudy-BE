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
    
# repo 생성
class GitHubCreateRepo(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data

        repo_name = data.get("name")
        description = data.get("description", "")
        auto_init = data.get("auto_init", True)

        if not repo_name:
            return Response({"error": "Repository name is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            access_token = decrypt_token(user.github_access_token)
        except Exception as e:
            return Response({"error": "Token decrypt failed", "detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        github_api_url = "https://api.github.com/user/repos"
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github+json",
        }

        payload = {
            "name": repo_name,
            "description": description,
            "private": False,     
            "auto_init": auto_init
        }

        res = requests.post(github_api_url, headers=headers, json=payload)

        try:
            response_data = res.json()
        except ValueError:
            return Response({
                "error": "GitHub returned non-JSON response",
                "raw_response": res.text
            }, status=status.HTTP_502_BAD_GATEWAY)

        if res.status_code != status.HTTP_201_CREATED:
            try:
                response_data = res.json()
                
                if res.status_code == 422 and any(
                    e.get("field") == "name" and "exists" in e.get("message", "")
                    for e in response_data.get("errors", [])
                ):
                    return Response({
                        "error": "Repo name already exists",
                        "code": "name_conflict"
                    }, status=409)
            except ValueError:
                return Response({
                    "error": "GitHub returned invalid response",
                    "raw": res.text
                }, status=502)
            
            return Response({
                "error": "GitHub repo creation failed",
                "status_code": res.status_code,
                "detail": response_data
            }, status=res.status_code)

        return Response({
            "message": "Public repository created successfully",
            "repo": {
                "name": response_data["name"],
                "full_name": response_data["full_name"],
                "html_url": response_data["html_url"],
                "default_branch": response_data["default_branch"],
            }
        }, status=status.HTTP_201_CREATED)

# 파일 내용 조회
class GitHubRepoFileContentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        repo_name = request.query_params.get("repo_name")
        branch = request.query_params.get("branch", "main")
        path = request.query_params.get("path", "")

        if not repo_name:
            return Response({"error": "Missing required parameter: repo_name"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            access_token = decrypt_token(user.github_access_token)
        except Exception as e:
            return Response({"error": "Token decrypt failed", "detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        github_username = user.username
        api_url = f"https://api.github.com/repos/{github_username}/{repo_name}/contents/{path}?ref={branch}"

        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        res = requests.get(api_url, headers=headers)
        if res.status_code != status.HTTP_200_OK:
            return Response({"error": "GitHub API error", "detail": res.json()}, status=res.status_code)

        item = res.json()

        if isinstance(item, list):
            # 디렉토리: 각 파일 내용 포함해서 반환
            files_data = []
            for file in item:
                content = None
                if file["type"] == "file" and file.get("download_url"):
                    file_res = requests.get(file["download_url"])
                    if file_res.status_code == 200:
                        content = file_res.text
                files_data.append({
                    "name": file["name"],
                    "path": file["path"],
                    "content": content
                })
            return Response({
                "repo": repo_name,
                "branch": branch,
                "path": path,
                "files": files_data
            }, status=status.HTTP_200_OK)

        elif isinstance(item, dict) and item.get("type") == "file":
            # 단일 파일 요청
            content = None
            if item.get("download_url"):
                file_res = requests.get(item["download_url"])
                if file_res.status_code == 200:
                    content = file_res.text
            return Response({
                "repo": repo_name,
                "branch": branch,
                "path": path,
                "file": {
                    "name": item["name"],
                    "path": item["path"],
                    "content": content
                }
            }, status=status.HTTP_200_OK)

        return Response({"error": "Unexpected GitHub API response"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)