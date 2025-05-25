import base64
import requests
import nacl.public
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from login.utils import decrypt_token

# GitHub Secrets 등록
class GitHubUploadSecrets(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data

        repo_name = data.get("repo_name")
        secrets = data.get("secrets")  

        if not repo_name or not secrets:
            return Response({
                "error": "Missing required fields (repo_name, secrets)"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            access_token = decrypt_token(user.github_access_token)
        except Exception as e:
            return Response({
                "error": "Token decrypt failed",
                "detail": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        github_username = user.username 
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github+json"
        }

        # Step 1. 공개키 조회
        key_url = f"https://api.github.com/repos/{github_username}/{repo_name}/actions/secrets/public-key"
        key_res = requests.get(key_url, headers=headers)

        try:
            key_data = key_res.json()
        except ValueError:
            return Response({
                "error": "GitHub returned non-JSON response while fetching public key",
                "raw_response": key_res.text
            }, status=status.HTTP_502_BAD_GATEWAY)

        if key_res.status_code != 200:
            return Response({
                "error": "Failed to fetch public key",
                "status_code": key_res.status_code,
                "detail": key_data
            }, status=key_res.status_code)

        public_key = key_data.get("key")
        key_id = key_data.get("key_id")
        if not public_key or not key_id:
            return Response({
                "error": "Invalid public key response from GitHub",
                "detail": key_data
            }, status=status.HTTP_502_BAD_GATEWAY)

        # Step 2. 각 secret 암호화 후 업로드
        failed = []
        for name, value in secrets.items():
            try:
                encrypted = self.encrypt_secret(public_key, value)
                secret_url = f"https://api.github.com/repos/{github_username}/{repo_name}/actions/secrets/{name}"
                payload = {
                    "encrypted_value": encrypted,
                    "key_id": key_id
                }

                secret_res = requests.put(secret_url, headers=headers, json=payload)
                if secret_res.status_code not in (201, 204):
                    failed.append({
                        name: secret_res.json()
                    })
            except Exception as e:
                failed.append({
                    name: {"exception": str(e)}
                })

        if failed:
            return Response({
                "error": "Some secrets failed to upload",
                "detail": failed
            }, status=status.HTTP_207_MULTI_STATUS)

        return Response({
            "message": f"Secrets uploaded to '{repo_name}'",
            "secrets": list(secrets.keys()),
            "github_url": f"https://github.com/{github_username}/{repo_name}/settings/secrets/actions"
        }, status=status.HTTP_201_CREATED)

    def encrypt_secret(self, public_key: str, secret_value: str) -> str:
        """GitHub의 base64 공개키로 암호화된 secret 반환"""
        public_key_bytes = base64.b64decode(public_key)
        sealed_box = nacl.public.SealedBox(nacl.public.PublicKey(public_key_bytes))
        encrypted = sealed_box.encrypt(secret_value.encode())
        return base64.b64encode(encrypted).decode("utf-8")

