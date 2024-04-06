from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.db.models import F
from django.contrib import messages
from django.db.models import Count
from .models import User, Article, Category, ModeratorRequest
from .forms import ArticleForm, ModeratorRequestForm, CategoryForm, LoginForm, CustomUserCreationForm
import random
import string


User = get_user_model()


def home(request):
    articles = Article.objects.all()
    return render(request, 'home.html', {'articles': articles})


def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))


@login_required
def lock_article(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if request.method == 'POST':
        if not article.is_locked:
            article.is_locked = True
            article.lock_reason = request.POST.get('lock_reason', '')
            article.save()
    return redirect('article_detail', pk=pk)


@login_required
def unlock_article(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if request.method == 'POST':
        if article.is_locked:
            article.is_locked = False
            article.lock_reason = ''
            article.save()
    return redirect('article_detail', pk=pk)


@login_required
@login_required
def delete_article(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if request.method == 'POST':
        # Получаем категории, к которым относится статья
        categories = article.categories.all()
        # Удаляем статью
        article.delete()
        # Обновляем счетчики статей в категориях
        for category in categories:
            # Получаем количество статей в данной категории
            article_count = Article.objects.filter(categories=category).count()
            # Обновляем счетчик статей в категории
            category.article_count = article_count
            category.save()
        return redirect('home')
    return render(request, 'confirm_article_deletion.html', {'article': article})


@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    moderator_requests = ModeratorRequest.objects.filter(is_approved=False)
    moderators = User.objects.filter(
        is_moderator=True) if hasattr(User, 'is_moderator') else []
    action = None  # устанавливаем значение по умолчанию
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')
        request_obj = get_object_or_404(ModeratorRequest, pk=request_id)
        if action == 'approve':
            request_obj.is_approved = True
            if hasattr(request_obj.user, 'is_moderator'):
                request_obj.user.is_moderator = True
                request_obj.user.save()
                # Генерируем случайный пароль для нового модератора
                new_password = generate_random_password()
                # Сохраняем сгенерированный пароль в модели пользователя
                request_obj.user.set_password(new_password)
                request_obj.user.save()
                send_mail(
                    'Ваш запрос на модератора одобрен',
                    f'Ваш новый пароль модератора: {new_password}',
                    'PyMasterWebNEW@yandex.ru',
                    [request_obj.email],
                    fail_silently=False,
                )
            else:
                request_obj.user.is_moderator = True
                request_obj.user.save()
                # Генерируем случайный пароль для нового модератора
                new_password = generate_random_password()
                # Сохраняем сгенерированный пароль в модели пользователя
                request_obj.user.set_password(new_password)
                request_obj.user.save()
                send_mail(
                    'Ваш запрос на модератора одобрен',
                    f'Ваш новый пароль модератора: {new_password}',
                    'PyMasterWebNEW@yandex.ru',
                    [request_obj.email],
                    fail_silently=False,
                )
            # Сохраняем изменения в объекте ModeratorRequest
            request_obj.save()
        elif action == 'reject':
            request_obj.is_approved = False
            request_obj.rejection_reason = request.POST.get('rejection_reason')
            send_mail(
                'Ваш запрос на модератора отклонен',
                f'Причина: {request_obj.rejection_reason}',
                'PyMasterWebNEW@yandex.ru',
                [request_obj.email],
                fail_silently=False,
            )
            # Сохраняем изменения в объекте ModeratorRequest
            request_obj.save()

    return render(request, 'admin_dashboard.html', {'moderator_requests': moderator_requests, 'moderators': moderators, 'action': action})


@login_required
def moderator_dashboard(request):
    articles = Article.objects.filter(
        author=request.user) | Article.objects.filter(editors=request.user)
    locked_articles = Article.objects.filter(is_locked=True)
    if request.method == 'POST':
        article_id = request.POST.get('article_id')
        action = request.POST.get('action')
        article = get_object_or_404(Article, pk=article_id)
        if action == 'lock':
            article.is_locked = True
            article.lock_reason = request.POST.get('lock_reason')
        elif action == 'unlock':
            article.is_locked = False
            article.lock_reason = ''
        article.save()
    return render(request, 'moderator_dashboard.html', {'articles': articles, 'locked_articles': locked_articles})


def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    return render(request, 'article_detail.html', {'article': article})


@login_required
def create_article(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            article.categories.set(form.cleaned_data['categories'])
            return redirect('article_detail', pk=article.pk)
    else:
        form = ArticleForm()
    return render(request, 'create_article.html', {'form': form})


@login_required
def edit_article(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if article.is_locked:
        return redirect('article_detail', pk=article.pk)
    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            article.version_history = f"{article.version_history}\n{article.content}"
            article = form.save(commit=False)
            article.editors.add(request.user)
            article.save()
            article.categories.set(form.cleaned_data['categories'])
            return redirect('article_detail', pk=article.pk)
    else:
        form = ArticleForm(instance=article)
    return render(request, 'edit_article.html', {'form': form, 'article': article})


@login_required
def become_moderator(request):
    if request.method == 'POST':
        form = ModeratorRequestForm(request.POST)
        if form.is_valid():
            # Создаем экземпляр запроса модератора
            moderator_request = form.save(commit=False)
            # Устанавливаем пользователя
            moderator_request.user = request.user
            moderator_request.save()

            # Отправляем уведомление по электронной почте
            send_mail(
                'Новый запрос на модератора',
                f'Новый запрос на модератора был подан пользователем {request.user.username}.',
                'PyMasterWebNEW@yandex.ru',
                ['PyMasterWebNEW@yandex.ru'],
                fail_silently=False,
            )

            return redirect('home')
    else:
        # Передайте значение пользователя при инициализации формы
        form = ModeratorRequestForm(initial={'user': request.user})
    return render(request, 'become_moderator.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_staff)
def category_management(request):
    categories = Category.objects.annotate(num_articles=Count('article'))
    if request.method == 'POST':
        # Проверяем, отправлена ли форма удаления категории
        if 'delete_category' in request.POST:
            category_id = request.POST.get('delete_category')
            category = get_object_or_404(Category, pk=category_id)
            if category.article_set.count() > 0:
                messages.error(
                    request, "Нельзя удалить категорию, содержащую статьи.")
            else:
                category.delete()
                messages.success(request, "Категория успешно удалена.")
            return redirect('category_management')
        # Если форма удаления не отправлена, продолжаем как обычно
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            return redirect('category_management')
    else:
        form = CategoryForm()

    return render(request, 'category_management.html', {'categories': categories, 'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        if request.user.check_password(old_password):
            request.user.set_password(new_password)
            request.user.save()
            login(request, request.user)
            return redirect('home')
    return render(request, 'change_password.html')


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')  # Измените на вашу главную страницу
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


def privacy_policy(request):
    return render(request, 'privacy_policy.html')
