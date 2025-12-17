from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Profile, Thread, Post
from forum.utils.html_sanitizer import sanitize_html

User = get_user_model()

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Потрібен дійсний email")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email")


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("avatar", "bio", "location", "website")
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3}),
        }

class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ("title", "category")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Заголовок теми..."}),
            "category": forms.Select(attrs={"class": "form-select"}),
        }

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
            })
        }

    def clean_content(self):
        raw_html = self.cleaned_data.get("content", "")

        if not raw_html.strip():
            raise forms.ValidationError("Повідомлення не може бути порожнім.")

        safe_html = sanitize_html(raw_html)

        # додаткова перевірка: після очистки не повинно стати порожньо
        if not safe_html.strip():
            raise forms.ValidationError("Контент містить недопустимі елементи.")

        return safe_html

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("avatar", "bio", "location", "website")
        widgets = {"bio": forms.Textarea(attrs={"rows": 3})}