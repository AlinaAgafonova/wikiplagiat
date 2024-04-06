from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.crypto import get_random_string
from django_ckeditor_5.fields import CKEditor5Field


class User(AbstractUser):
    is_moderator = models.BooleanField(default=False)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        related_query_name='custom_user',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        related_query_name='custom_user',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def set_moderator_password(self):
        self.set_password(get_random_string(length=12))
        self.save()


class Article(models.Model):
    title = models.CharField(max_length=200)
    content = CKEditor5Field(
        verbose_name='Полное описание', config_name='extends')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        'auth.User', on_delete=models.CASCADE, related_name='created_articles')
    editors = models.ManyToManyField(
        'auth.User', related_name='edited_articles')
    categories = models.ManyToManyField('Category')
    is_locked = models.BooleanField(default=False)
    lock_reason = models.CharField(max_length=500, blank=True, null=True)
    version_history = models.TextField(blank=True, null=True)


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    article_count = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class ModeratorRequest(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    email = models.EmailField()
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    rejection_reason = models.CharField(max_length=500, blank=True, null=True)
