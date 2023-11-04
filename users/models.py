from django.db import models
from django.contrib.auth.models import User
from django_softdelete.models import SoftDeleteModel, SoftDeleteManager
from .constants import NEWS_CATEGORY_CHOICES
from multiselectfield import MultiSelectField


class AppManager(SoftDeleteManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class PostCheck(SoftDeleteModel):
    title = models.CharField(max_length=255)
    content = models.TextField()
    link = models.URLField(max_length=255)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)
    status = models.BooleanField(default=False)
    objects = AppManager()

    def __str__(self):
        return self.title


class UserProfile(SoftDeleteModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    news_categories_like = MultiSelectField(
        choices=NEWS_CATEGORY_CHOICES, max_length=200
    )

    def __str__(self):
        return self.user.username
