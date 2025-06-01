import os
import shutil
import json
import requests
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import Project
from .utils import generate_tfvars 
from django.contrib.auth import get_user_model

User = get_user_model()

# 템플릿과 프로젝트 생성 경로
TEMPLATE_ROOT = os.path.join(settings.BASE_DIR, 'terraform_templates')
USER_PROJECT_ROOT = os.path.join(settings.BASE_DIR, 'user_projects')  # 실제 .tf가 저장되는 곳

class ProjectCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        name = request.data.get("project_name")
        description = request.data.get("description")
        template_name = request.data.get("template_name")
        custom_values = request.data.get("custom_values", {})

        # 1. 템플릿 경로 확인
        template_path = os.path.join(TEMPLATE_ROOT, template_name)
        if not os.path.exists(template_path):
            return Response({"error": "Invalid template"}, status=400)

        # 2. metadata.json 로드 및 custom_values 키 검증
        metadata_path = os.path.join(template_path, "metadata.json")
        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            expected_keys = {item["name"] for item in metadata.get("variables", [])}
        except Exception as e:
            return Response({"error": "Invalid metadata.json"}, status=500)

        missing_keys = expected_keys - custom_values.keys()
        if missing_keys:
            return Response({"error": f"Missing custom_values: {missing_keys}"}, status=400)

        # 3. 사용자 전용 프로젝트 디렉토리 생성
        user_project_dir = os.path.join(USER_PROJECT_ROOT, f"{user.username}_{name}")
        os.makedirs(user_project_dir, exist_ok=True)

        # 4. 템플릿 파일 복사
        for file_name in os.listdir(template_path):
            if file_name.endswith(".tf") or file_name.endswith(".tf.json"):
                shutil.copy(
                    os.path.join(template_path, file_name),
                    os.path.join(user_project_dir, file_name)
                )

        # 5. terraform.tfvars 생성
        tfvars_content = generate_tfvars(custom_values)
        with open(os.path.join(user_project_dir, "terraform.tfvars"), "w") as f:
            f.write(tfvars_content)

        # 6. 프로젝트 DB 저장
        project = Project.objects.create(
            user=user,
            name=name,
            description=description,
            template_name=template_name,
            tfvars=json.dumps(custom_values),
            project_path=user_project_dir,
        )

        return Response({"message": "Project created", "project_id": project.id}, status=201)
