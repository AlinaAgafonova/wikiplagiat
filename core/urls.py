from django.urls import path, include
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path("ckeditor5/", include('django_ckeditor_5.urls'),
         name="ck_editor_5_upload_file"),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('moderator_dashboard/', views.moderator_dashboard,
         name='moderator_dashboard'),
    path('article/<int:pk>/', views.article_detail, name='article_detail'),
    path('create_article/', views.create_article, name='create_article'),
    path('edit_article/<int:pk>/', views.edit_article, name='edit_article'),
    path('article/<int:pk>/lock/', views.lock_article, name='lock_article'),
    path('article/<int:pk>/unlock/', views.unlock_article, name='unlock_article'),
    path('delete_article/<int:pk>/', views.delete_article, name='delete_article'),
    path('become_moderator/', views.become_moderator, name='become_moderator'),
    path('category_management/', views.category_management,
         name='category_management'),
    path('change_password/', views.change_password, name='change_password'),
    path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
]
