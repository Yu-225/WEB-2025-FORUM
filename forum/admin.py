from django.contrib import admin
from .models import Category, Thread, Post, Profile, PostLike

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'created_at')
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ('title', 'description')


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'pinned', 'closed', 'updated_at')
    list_filter = ('category', 'pinned', 'closed')
    search_fields = ('title', 'author__username')
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'thread', 'author', 'created_at')
    search_fields = ('content', 'author__username')
    list_filter = ('created_at',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'created_at')
    search_fields = ('user__username', 'user__email', 'location')


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    search_fields = ('user__username',)