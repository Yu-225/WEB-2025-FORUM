from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from ckeditor.fields import RichTextField 
from PIL import Image

# Create your models here.

User = get_user_model()

class Category(models.Model):
    title = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(null=True, blank=True)


    class Meta:
        ordering = ['title']
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"
        indexes = [models.Index(fields=['slug']),]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            # обмежуємо довжину slab
            self.slug = slugify(self.title)[:140]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('category', kwargs={'slug': self.slug})


class Thread(models.Model):
    # protect — щоб випадкове видалення категорії не прибирало теми
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='threads')
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=300, blank=True, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='threads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    pinned = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-pinned', '-updated_at']
        verbose_name = "Тема"
        verbose_name_plural = "Теми"
        indexes = [
            models.Index(fields=['-updated_at']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or 'thread'
            slug = base
            idx = 1
            
            while Thread.objects.filter(slug=slug).exists():
                slug = f"{base}-{idx}"
                idx += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('thread', args=[self.pk, self.slug])


class Post(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = RichTextField(config_name='default')
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')

    class Meta:
        ordering = ['created_at']
        verbose_name = "Пост"
        verbose_name_plural = "Пости"
        indexes = [
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Post #{self.pk} by {self.author}"

    def short(self, n=200):
        text = (self.content or '')
        # не намагаймося різати HTML — в demo вистачить plain cut
        plain = text if len(text) <= n else text[:n] + '...'
        return plain

    @property
    def likes_count(self):
        return self.likes.count()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=120, blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Профіль"
        verbose_name_plural = "Профілі"

    def __str__(self):
        return f"Profile: {self.user.username}"
    
    def save(self, *args, **kwargs):
        # зберігаємо модель спочатку (щоб поле avatar було записано у файлову систему)
        super().save(*args, **kwargs)

        if self.avatar:
            try:
                img_path = self.avatar.path
                img = Image.open(img_path)
                # вибір ресемплу залежно від Pillow версії
                resample = getattr(Image, 'Resampling', Image).LANCZOS if hasattr(Image, 'Resampling') else Image.ANTIALIAS
                max_size = (400, 400)  # рекомендований макс розмір
                img.thumbnail(max_size, resample)
                img.save(img_path)
            except Exception:
                # не фейлимо запит — якщо щось піде не так, просто пропустимо
                pass


class PostLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')
        verbose_name = "Лайк"
        verbose_name_plural = "Лайки"
        indexes = [models.Index(fields=['post', 'user']),]

    def __str__(self):
        return f"{self.user} -> post#{self.post_id}"