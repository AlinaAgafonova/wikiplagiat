from django.db.models.signals import m2m_changed
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Article, Category  # Импортируем модель Article


@receiver(m2m_changed, sender=Article.categories.through)
def update_category_article_count(sender, instance, action, **kwargs):
    if action == 'post_add' or action == 'post_remove' or action == 'post_clear':
        for category in instance.categories.all():
            category.article_count = category.article_set.count()
            category.save()


@receiver(post_delete, sender=Article)
def update_category_article_count_on_delete(sender, instance, **kwargs):
    for category in instance.categories.all():
        category.article_count = category.article_set.count()
        category.save()
