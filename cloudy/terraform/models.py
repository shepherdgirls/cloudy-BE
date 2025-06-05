from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()
class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")

    project_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    repo_name = models.CharField(max_length=100, blank=True, null=True)  

    template_name = models.CharField(max_length=100)  # ex: ec2_rds_alb
    custom_values = models.JSONField()  # tfvars로 넘길 사용자 커스텀 값

    project_dir = models.TextField()  # user_projects/경로

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        username = getattr(self.user, 'username', None)
        github_id = getattr(self.user, 'github_id', None)
        return f"{self.project_name} by {username or github_id or 'unknown'}"
