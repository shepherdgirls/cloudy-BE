import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .utils import get_tokens_for_user, encrypt_token
from urllib.parse import urlencode

User = get_user_model()

class GitHubOAuthURLView(APIView):
    def get(self, request):
        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": settings.GITHUB_CALLBACK_URL,
            "scope": "read:user user:email workflow public_repo admin:repo_hook",
        }
        github_auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
        return Response({"url": github_auth_url})


class GitHubLogin(APIView):
    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response({"error": "code is required"}, status=400)

        # 1. access token 요청
        token_res = requests.post("https://github.com/login/oauth/access_token", headers={
            "Accept": "application/json"
        }, data={
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code
        })
        token_json = token_res.json()
        access_token = token_json.get("access_token")

        if not access_token:
            return Response({"error": "invalid code", "details": token_json}, status=400)

        # 2. 사용자 정보 요청
        user_info = requests.get("https://api.github.com/user", headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }).json()

        github_id = user_info.get("id")
        username = user_info.get("login")
        avatar_url = user_info.get("avatar_url")
        email = user_info.get("email") 

        # 이메일(비공개 시) 별도 API 호출
        if not email:
            email_list = requests.get("https://api.github.com/user/emails", headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }).json()
            for e in email_list:
                if e.get("primary") and e.get("verified"):
                    email = e.get("email")
                    break   

        if not github_id or not username:
            return Response({"error": "GitHub user info not valid", "details": user_info}, status=400)

        # 3. 사용자 생성 or 조회
        user, created = User.objects.get_or_create(
            github_id=github_id,
            defaults={
                "username": username,
                "email": email,
                "github_avatar_url": avatar_url,
                "github_access_token": encrypt_token(access_token),
            }
        )

        # 이미 존재하는 경우 access_token 갱신
        if not created:
            user.github_access_token = encrypt_token(access_token)
            user.save()

        # 4. JWT 발급
        tokens = get_tokens_for_user(user)

        return Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "github_avatar_url": user.github_avatar_url,
                "created_at": user.created_at,
            },
            "tokens": tokens
        })
    
    
# 마이페이지
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        data = {
            "username": user.username,
            "email": user.email,
            "github_avatar_url": user.github_avatar_url,}
        
        return Response(data)