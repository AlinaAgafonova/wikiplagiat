from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from ckeditor.widgets import CKEditorWidget
from .models import Article, Category, ModeratorRequest


User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    is_moderator = forms.BooleanField(
        initial=False, required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = _(
            'Логин должен быть не более 150 символов. Только буквы, цифры и @/./+/-/_.')
        self.fields['password1'].help_text = _(
            'Ваш пароль не должен быть слишком похож на другую вашу личную информацию и должен содержать как минимум 8 символов.')
        self.fields['password2'].help_text = _(
            'Повторите ваш пароль для проверки.')
        self.fields['password1'].label = _('Введите пароль')
        self.fields['password2'].label = _('Повторите пароль')

    def clean_is_moderator(self):
        return False

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'password1', 'password2', 'is_moderator')
        labels = {
            'username': 'Логин'
        }


class ArticleForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(), to_field_name='name', label='Категории', required=False)
    content = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = Article
        fields = ['title', 'content', 'categories']
        labels = {
            'title': 'Заголовок',
            'content': 'Содержание',
        }


class ModeratorRequestForm(forms.ModelForm):
    class Meta:
        model = ModeratorRequest
        fields = ['email', 'reason']
        labels = {
            'email': 'Ваша почта',
            'reason': 'Причина',
        }

    user = forms.ModelChoiceField(
        queryset=User.objects.all(), widget=forms.HiddenInput())

    def clean_user(self):
        user = self.cleaned_data.get('user')
        if not user:
            raise forms.ValidationError('Пользователь не указан')
        return user

    def save(self, commit=True):
        instance = super().save(commit=False)
        user = self.cleaned_data['user']
        instance.user = user
        if commit:
            instance.save()
        return instance


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        labels = {
            'name': 'Название категории',
        }


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Логин', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(
        label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError('Неверный логин или пароль')

        return cleaned_data
