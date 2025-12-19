import math
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.template.loader import render_to_string

from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch
from django.urls import reverse, NoReverseMatch

from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta

import logging

from myforum import settings

from .forms import ThreadForm, PostForm, ProfileForm, UserUpdateForm, RegisterForm
from .models import PostLike, Profile, Thread, Post, Category

logger = logging.getLogger(__name__)
User = get_user_model()


def _is_htmx(request):
    """
    Надійно перевіряє чи запит — від htmx.
    Повертає True тільки коли заголовок явно 'true' або '1'.
    """
    hx = request.headers.get('HX-Request') or request.META.get('HTTP_HX_REQUEST')
    if hx is None:
        return False
    return str(hx).lower() in ('true', '1')



def index(request):
    qs = Thread.objects.select_related('author', 'category') \
        .annotate(posts_count=Count('posts')) \
        .order_by('-pinned', '-updated_at')

    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    threads = paginator.get_page(page)

    popular_threads = Thread.objects.select_related('author', 'category') \
        .annotate(posts_count=Count('posts')) \
        .order_by('-views', '-updated_at')[:5]

    recent_posts = Post.objects.select_related('author', 'thread') \
        .order_by('-created_at')[:5]

    categories = Category.objects.annotate(threads_count=Count('threads')).order_by('title')

    since = timezone.now() - timedelta(minutes=15)
    users_online_qs = User.objects.filter(last_login__gte=since).order_by('-last_login')[:10]
    users_online_count = users_online_qs.count()

    context = {
        'threads': threads,
        'popular_threads': popular_threads,
        'recent_posts': recent_posts,
        'categories': categories,
        'users_online': users_online_qs,
        'users_online_count': users_online_count,
    }
    
    
    hero_backgrounds = getattr(settings, "HERO_BACKGROUNDS", []) or []
    hero_mode = getattr(settings, "HERO_BG_MODE", "rotate")
    hero_autoplay_delay = getattr(settings, "HERO_BG_AUTOPLAY_DELAY", 6000)
    hero_fade_speed = getattr(settings, "HERO_BG_FADE_SPEED", 800)

    hero_selected = None
    if hero_backgrounds:
        if hero_mode == "random":
            hero_selected = random.randrange(len(hero_backgrounds))
        else:
            hero_selected = 0 

    context.update({
        'hero_backgrounds': hero_backgrounds,
        'hero_mode': hero_mode,
        'hero_selected': hero_selected,
        'hero_autoplay_delay': hero_autoplay_delay,
        'hero_fade_speed': hero_fade_speed,
    })
    
    
    return render(request, 'forum/index.html', context)

def custom_404(request, exception):
    return render(request, "errors/404.html", status=404)


def category_page(request, slug):
    category = get_object_or_404(Category, slug=slug)

    posts_prefetch = Prefetch(
        'posts',
        queryset=Post.objects.select_related('author').order_by('-created_at'),
        to_attr='prefetched_posts'
    )

    threads_qs = (
        category.threads
        .select_related('author', 'category')
        .prefetch_related(posts_prefetch)
        .annotate(posts_count=Count('posts'))
        .order_by('-pinned', '-updated_at')
    )

    # пагінація
    paginator = Paginator(threads_qs, 15)
    threads_page = paginator.get_page(request.GET.get('page'))

    for t in threads_page:
        t.last_post = (t.prefetched_posts[0] if getattr(t, 'prefetched_posts', None) else None)
        try:
            uname = getattr(t.author, 'username', None)
            t.author_profile_url = reverse('profile_view', args=[uname]) if uname else '#'
        except NoReverseMatch:
            t.author_profile_url = '#'

    categories = Category.objects.annotate(topics=Count('threads')).order_by('title')
    top_users = User.objects.annotate(posts_count=Count('posts')).order_by('-posts_count')[:6]

    context = {
        'category': category,
        'threads': threads_page,
        'categories': categories,
        'top_users': top_users,
    }
    return render(request, 'forum/category.html', context)



def thread_page(request, pk, slug=None):
    thread = get_object_or_404(
        Thread.objects.select_related('author', 'category'),
        pk=pk
    )

    # права
    can_edit_thread = (
        request.user.is_authenticated
        and (request.user == thread.author or request.user.is_staff)
    )
    can_reply = request.user.is_authenticated and not thread.closed

    # posts + пагінація
    posts_qs = (
        thread.posts
        .select_related('author')
        .prefetch_related('likes') 
        .order_by('created_at')
    )

    paginator = Paginator(posts_qs, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)

    for p in posts:
        p.can_edit = (
            request.user.is_authenticated
            and (request.user == p.author or request.user.is_staff)
        )
        try:
            username = p.author.username
            p.author_profile_url = reverse('profile_view', args=[username])
        except NoReverseMatch:
            p.author_profile_url = '#'

        # лайки
        if request.user.is_authenticated:
            p.liked = p.likes.filter(user=request.user).exists()
        else:
            p.liked = False

    context = {
        'thread': thread,
        'posts': posts,
        'post_form': PostForm(),
        'thread_can_edit': can_edit_thread,
        'thread_can_reply': can_reply,
        'request_user': request.user,
    }

    return render(request, 'forum/thread.html', context)



@login_required
def new_thread_page(request):
    if request.method == 'POST':
        tform = ThreadForm(request.POST)
        pform = PostForm(request.POST)
        if tform.is_valid() and pform.is_valid():
            thread = tform.save(commit=False)
            thread.author = request.user
            thread.save()
            post = pform.save(commit=False)
            post.thread = thread
            post.author = request.user
            post.save()
            return redirect(thread.get_absolute_url())
    else:
        tform = ThreadForm()
        pform = PostForm()
    return render(request, 'forum/new_thread.html', {'thread_form': tform, 'post_form': pform})



@require_POST
@login_required
def post_create_htmx(request, thread_pk):
    logger.debug("post_create_htmx: HX header = %s", request.META.get('HTTP_HX_REQUEST'))
    logger.debug("post_create_htmx: All headers: %s", {k:v for k,v in request.META.items() if k.startswith('HTTP_')})
    
    thread = get_object_or_404(Thread, pk=thread_pk)
    form = PostForm(request.POST)
    is_htmx = _is_htmx(request)
    logger.debug("post_create_htmx: is_htmx=%s, user=%s, thread=%s", is_htmx, request.user, thread_pk)

    if not form.is_valid():
        logger.debug("post_create_htmx: form invalid: %s", form.errors.as_json())
        if is_htmx:
            html = render_to_string('forum/_post_form.html', {'form': form, 'thread': thread}, request=request)
            return HttpResponse(html, status=400)
        return redirect(thread.get_absolute_url())

    # save post
    post = form.save(commit=False)
    post.thread = thread
    post.author = request.user
    post.save()
    logger.debug("post_create_htmx: saved post id=%s", post.pk)

    total_posts = thread.posts.count()
    PAGE_SIZE = 10
    last_page = math.ceil(total_posts / PAGE_SIZE) if total_posts else 1

    try:
        current_page = int(request.POST.get('current_page', 1))
    except (TypeError, ValueError):
        current_page = 1

    if is_htmx:
        if current_page != last_page:
            resp = HttpResponse(status=204)
            resp['HX-Redirect'] = f"{thread.get_absolute_url()}?page={last_page}#post-{post.pk}"
            return resp

        html = render_to_string('forum/_post.html', {
            'p': post,
            'request_user': request.user,
            'is_new': True,
            'last_page': last_page,
        }, request=request)
        return HttpResponse(html, content_type='text/html')

    return redirect(f"{thread.get_absolute_url()}?page={last_page}#post-{post.pk}")



@require_POST
@login_required
def add_post(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id)

    content = request.POST.get("content", "").strip()
    if not content:
        return HttpResponse("", status=400)

    post = Post.objects.create(
        thread=thread,
        author=request.user,
        content=content,
    )
    
    if request.headers.get("HX-Request"):
        html = render_to_string(
            "partials/post_item.html",
            {
                "post": post,
                "user": request.user,
                "is_new": True,
                "last_page": thread.last_page(),
            },
            request=request,
        )
        return HttpResponse(html)

    return redirect(thread.get_absolute_url())



@require_POST
@login_required
def toggle_like(request, pk):
    post = get_object_or_404(Post, pk=pk)

    like, created = PostLike.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    likes_count = PostLike.objects.filter(post=post).count()

    if _is_htmx(request):
        html = render_to_string('forum/_post_like.html', {
            'post': post,
            'liked': liked,
            'likes_count': likes_count,
        }, request=request)
        return HttpResponse(html)

    return redirect(post.thread.get_absolute_url())



@login_required
def edit_thread(request, pk):
    thread = get_object_or_404(Thread, pk=pk)
    if not (request.user == thread.author or request.user.is_staff):
        return HttpResponseForbidden("Немає прав редагувати цю тему.")
    if request.method == 'POST':
        form = ThreadForm(request.POST, instance=thread)
        if form.is_valid():
            form.save()
            messages.success(request, "Тему оновлено.")
            return redirect(thread.get_absolute_url())
    else:
        form = ThreadForm(instance=thread)
    return render(request, "forum/edit_thread.html", {"form": form, "thread": thread})



@login_required
def delete_thread(request, pk):
    thread = get_object_or_404(Thread, pk=pk)
    if not (request.user == thread.author or request.user.is_staff):
        return HttpResponseForbidden("Немає прав видаляти цю тему.")
    if request.method == 'POST':
        thread.delete()
        messages.success(request, "Тему видалено.")
        return redirect('categories')
    return render(request, "forum/confirm_delete_thread.html", {"thread": thread})



@login_required
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if not (request.user == post.author or request.user.is_staff):
        return HttpResponseForbidden("Немає прав редагувати цей пост.")
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.edited_at = timezone.now()
            post.save()
            messages.success(request, "Пост оновлено.")
            return redirect(post.thread.get_absolute_url())
    else:
        form = PostForm(instance=post)
    return render(request, "forum/edit_post.html", {"form": form, "post": post})



@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if not (request.user == post.author or request.user.is_staff):
        return HttpResponseForbidden("Немає прав видаляти цей пост.")
    if request.method == 'POST':
        thread_url = post.thread.get_absolute_url()
        post.delete()
        messages.success(request, "Пост видалено.")
        return redirect(thread_url)
    return render(request, "forum/confirm_delete_post.html", {"post": post})



def profile_page(request, username=None):
    if username:
        profile_user = get_object_or_404(User, username=username)
    else:
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        profile_user = request.user

    posts = Post.objects.filter(author=profile_user).select_related('thread').order_by('-created_at')[:10]

    posts_count = Post.objects.filter(author=profile_user).count()
    threads_count = Thread.objects.filter(author=profile_user).count()

    context = {
        'profile_user': profile_user,
        'profile': profile_user,  # backward compatibility for templates using 'profile'
        'posts': posts,
        'posts_count': posts_count,
        'threads_count': threads_count,
        'is_owner': request.user.is_authenticated and request.user == profile_user,
    }
    return render(request, 'forum/profile.html', context)



@login_required
def profile_edit_page(request):
    user = request.user
    profile = getattr(user, 'profile', None)
    if profile is None:
        profile = Profile.objects.create(user=user)

    if request.method == 'POST':
        uform = UserUpdateForm(request.POST, instance=user)
        pform = ProfileForm(request.POST, request.FILES, instance=profile)
        if uform.is_valid() and pform.is_valid():
            uform.save()
            pform.save()
            messages.success(request, "Профіль оновлено.")
            return redirect('profile')
        else:
            messages.error(request, "Будь ласка, виправте помилки у формі.")
    else:
        uform = UserUpdateForm(instance=user)
        pform = ProfileForm(instance=profile)

    return render(request, 'forum/profile_edit.html', {
        'user_form': uform,
        'profile_form': pform,
    })



def categories_list_page(request):
    categories = Category.objects.annotate(threads_count=Count('threads')).order_by('title')
    is_admin = request.user.is_authenticated and request.user.is_staff
    context = {"categories": categories, "is_admin": is_admin}
    return render(request, "forum/categories.html", context)



def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Реєстрація успішна. Ласкаво просимо!")
            return redirect('profile')
    else:
        form = RegisterForm()
    return render(request, 'forum/register.html', {'form': form})



def about_page(request):
    developer = {
        "name": "Юрій Лапін",
        "role": "Студент, розробник (Комп'ютерні науки)",
        "location": "Львів, Україна",
        "email": "Yurii.Lapin.PP.2024@lpnu.ua",
        "photo": "/static/img/about/dev-photo.jpg",
        "facts": [
            "Навчаюся на 2 курсі, спеціальність Комп'ютерні науки.",
            "Працював над декількома навчальними проєктами на Django і FastAPI.",
            "Люблю інді-ігри",
            "НЕ люблю мед !!!",
        ],
        "social": {
            "github": "https://github.com/Yu-225",
            "linkedin": "https://www.linkedin.com/in/yu-lapin-064902255/",
        }
    }

    site_info = {
        "title": "БочкаМеду",
        "summary": "Міні-форум для обговорення ігор — UI-first, навчальний проєкт.",
        "technologies": [
            "Python - Django",
            "HTMX (dynamic partial updates)",
            "Bootstrap 5",
            "Quill Rich Text Editor",
            "SQLite (dev) ",
        ],
        "features": [
            "Створення тем",
            "Лайки, редагування постів, профілі",
            "HTMX для плавного UX без повних перезавантажень",
        ],
        "github": "https://github.com/",
        "license": "MIT",
    }

    context = {
        "developer": developer,
        "site_info": site_info,
    }
    return render(request, "forum/about.html", context)



def rules_page(request):
    rules = [
        {"title": "Дотримуйся поваги", "text": "Не допускаємо образ, ненависті, приниження. Обговорюємо аргументовано."},
        {"title": "Чіткі теми", "text": "Створюй зрозумілі заголовки, додавай опис та теги."},
        {"title": "Без спаму", "text": "Реклама і спам заборонені; рекламні пости погоджуй з модерацією."},
        {"title": "Публічність контенту", "text": "Уникай публікації приватних даних інших людей."},
        {"title": "Дотримуйся законів", "text": "Не публікуй незаконний або небезпечний контент."},
    ]
    return render(request, "forum/rules.html", {"rules": rules})



def faq_page(request):
    faqs = [
        # Загальні
        {
            "q": "Що це за форум?",
            "a": "Це форум для обговорення ігор: новини, думки, гайди, інді та AAA-проєкти. Місце для спокійного й змістовного спілкування."
        },
        {
            "q": "Для кого створений цей форум?",
            "a": "Для геймерів, розробників, ентузіастів та всіх, хто хоче обговорювати ігри без токсичності."
        },
        {
            "q": "Чи можна користуватися форумом без реєстрації?",
            "a": "Так, переглядати теми можна без акаунту. Для створення тем і повідомлень потрібна реєстрація."
        },

        # Реєстрація
        {
            "q": "Чи потрібно реєструватись?",
            "a": "Так, щоб писати повідомлення, ставити лайки та створювати теми."
        },
        {
            "q": "Що робити, якщо я забув пароль?",
            "a": "Скористайся формою відновлення пароля на сторінці входу."
        },
        {
            "q": "Чи можна видалити акаунт?",
            "a": "Так, через налаштування профілю або звернувшись до адміністрації."
        },

        # Профіль
        {
            "q": "Як змінити аватар?",
            "a": "Зайди у Профіль → Редагувати та обери новий аватар."
        },
        {
            "q": "Яку інформацію бачать інші користувачі?",
            "a": "Нікнейм, аватар та активність на форумі. Особисті дані не публікуються."
        },

        # Теми та повідомлення
        {
            "q": "Як створити тему?",
            "a": "Перейди у потрібну категорію і натисни кнопку «Створити тему» або скористайся кнопкою на головній сторінці."
        },
        {
            "q": "У чому різниця між темою і повідомленням?",
            "a": "Тема — це обговорення. Повідомлення — відповіді всередині теми."
        },
        {
            "q": "Чи можна редагувати або видалити свій пост?",
            "a": "Так, якщо він ще не порушує правила та не закритий модератором."
        },
        {
            "q": "Чому я не можу відповісти в темі?",
            "a": "Ймовірно, тема закрита або ти не авторизований."
        },

        # Лайки
        {
            "q": "Як працюють лайки?",
            "a": "Ти можеш поставити або прибрати лайк під повідомленням. Кількість лайків показує популярність поста."
        },
        {
            "q": "Чи можна прибрати лайк?",
            "a": "Так, повторне натискання прибирає лайк."
        },
        {
            "q": "Чому кількість лайків не оновилась одразу?",
            "a": "Сторінка може оновлюватися асинхронно. Спробуй оновити сторінку."
        },

        # Модерація
        {
            "q": "Які основні правила форуму?",
            "a": "Заборонені образи, спам, реклама без дозволу та токсична поведінка."
        },
        {
            "q": "За що можуть забанити?",
            "a": "За систематичні порушення правил або серйозні інциденти."
        },
        {
            "q": "Чи можна оскаржити бан?",
            "a": "Так, звернувшись до адміністрації форуму."
        },

        # Технічні
        {
            "q": "Чи працює форум на мобільних пристроях?",
            "a": "Так, інтерфейс адаптований для смартфонів і планшетів."
        },
        {
            "q": "Що робити, якщо сайт працює некоректно?",
            "a": "Онови сторінку або повідом про помилку адміністрації."
        },

        # Інше
        {
            "q": "Чи плануються нові функції?",
            "a": "Так, форум активно розвивається. Пропозиції вітаються."
        },
        {
            "q": "Куди звертатися з питаннями?",
            "a": "Пиши у відповідну тему або звертайся до адміністратора через сторінку «Про проєкт»."
        },
    ]

    return render(request, "forum/faq.html", {"faqs": faqs})
