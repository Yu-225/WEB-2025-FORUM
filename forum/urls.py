# forum/urls.py
from django.urls import include, path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    
    # static/info pages
    path("about/", views.about_page, name="about"),
    path("rules/", views.rules_page, name="rules"),
    path("faq/", views.faq_page, name="faq"),
    
    # categories
    path("categories/", views.categories_list_page, name="categories"),
    path("c/<slug:slug>/", views.category_page, name="category"),
    
    # threads
    path('new-thread/', views.new_thread_page, name='new_thread'),
    path('t/<int:pk>/edit/', views.edit_thread, name='thread_edit'),
    path('t/<int:pk>/delete/', views.delete_thread, name='thread_delete'),
    path("t/<int:pk>/<slug:slug>/", views.thread_page, name="thread"),
    path('t/<int:thread_pk>/add-post/', views.post_create_htmx, name='post_create_htmx'),
    
    # posts
    path('post/<int:pk>/edit/', views.edit_post, name='post_edit'),
    path('post/<int:pk>/delete/', views.delete_post, name='post_delete'),
    
    # edits
    path('post/<int:pk>/edit/', views.edit_post, name='edit_post'),
    path('thread/<int:pk>/edit/', views.edit_thread, name='edit_thread'),
    
    # likes
    path('post/<int:pk>/like/', views.toggle_like, name='toggle_like'),
    
    # User profile
    path("profile/", views.profile_page, name="profile"),
    path("profile/edit/", views.profile_edit_page, name="profile_edit"),
    path("profile/<str:username>/", views.profile_page, name="profile_view"),
    
    # auth
    path("login/", auth_views.LoginView.as_view(template_name='forum/login.html'), name='login'),
    path("logout/", auth_views.LogoutView.as_view(next_page='index'), name='logout'),
   
    # registration
    path('register/', views.register_view, name='register'),
    
    # Password reset ( ще не робить ) )
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="forum/password_reset.html",
            email_template_name="forum/password_reset_email.html",
            subject_template_name="forum/password_reset_subject.txt",
            success_url="/password-reset/done/"
        ),
        name="password_reset"
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="forum/password_reset_done.html"),
        name="password_reset_done"
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="forum/password_reset_confirm.html",
            success_url="/password-reset/complete/"
        ),
        name="password_reset_confirm"
    ),
    path(
        "password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(template_name="forum/password_reset_complete.html"),
        name="password_reset_complete"
    ),
]
