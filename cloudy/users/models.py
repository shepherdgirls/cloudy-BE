from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    github_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    github_avatar_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    username = models.CharField(max_length=150, null=True, blank=True, unique=False)
    email = models.EmailField(null=True, blank=True)

    USERNAME_FIELD = 'github_id'  
    REQUIRED_FIELDS = []  

    def __str__(self):
        return self.username or f'github_{self.github_id}'