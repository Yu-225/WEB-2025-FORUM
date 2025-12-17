# forum/management/commands/create_demo_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from forum.models import Category, Thread, Post, Profile
from django.utils import timezone
from django.utils.text import slugify
import random

User = get_user_model()

class Command(BaseCommand):
    help = "Create demo categories, threads, posts and a test user (idempotent)"

    def handle(self, *args, **options):
        # 1) Тестовий користувач
        username = "testuser"
        password = "testpass123"
        user, created_user = User.objects.get_or_create(
            username=username,
            defaults={"email": "test@example.com"}
        )
        if created_user:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created user {username} / {password}"))
        else:
            self.stdout.write(self.style.WARNING("User testuser already exists"))

        # 2) Категорії
        cats = [
            ("development", "Розробка", "Питання та відповіді з програмування та веба"),
            ("general", "Загальні", "Обговорення різних тем"),
            ("life", "Життя", "Поради та лайфхаки"),
            ("resources", "Ресурси", "Підбірки корисних матеріалів"),
        ]
        created_cats = []
        for slug_val, title, desc in cats:
            # спробуємо знайти за title (у твоїй моделі title унікальний)
            cat = Category.objects.filter(title=title).first()
            if cat:
                self.stdout.write(self.style.WARNING(f"Category already exists: {title}"))
            else:
                # якщо немає — створюємо з певним slug (переконаємось, що унікальний)
                slug_candidate = slug_val
                # гарантуємо унікальність slug простим способом
                i = 0
                while Category.objects.filter(slug=slug_candidate).exists():
                    i += 1
                    slug_candidate = f"{slug_val}-{i}"
                cat = Category.objects.create(title=title, slug=slug_candidate, description=desc)
                self.stdout.write(self.style.SUCCESS(f"Created category {title} (slug={slug_candidate})"))
            created_cats.append(cat)

        # 3) Треди (idempotent) — не використовуємо get_or_create з полями, що можуть створити slug-колізію
        titles = [
            "Як почати вивчати Python?",
            "Кращі практики роботи з Git",
            "Де знайти ресурси для ML?",
            "Оптимізація запитів в БД",
            "Поради для інтерв'ю",
            "Домашні проєкти для портфоліо",
            "Як організувати час для навчання",
            "Кращі книги з програмування",
            "Ресурси для frontend",
            "Питання про деплой"
        ]

        threads = []
        for i, title in enumerate(titles):
            existing = Thread.objects.filter(title=title).first()
            if existing:
                self.stdout.write(self.style.WARNING(f"Thread already exists: {title}"))
                threads.append(existing)
                continue

            cat = created_cats[i % len(created_cats)]
            # генеруємо унікальний slug: base + timestamp + random
            base = slugify(title)[:150]
            ts = int(timezone.now().timestamp())
            rand = random.randint(1000, 9999)
            slug_candidate = f"{base}-{ts}-{rand}"
            # якщо рідко все ж таки зайнято — додаємо суфікс-лічильник
            suffix = 0
            while Thread.objects.filter(slug=slug_candidate).exists():
                suffix += 1
                slug_candidate = f"{base}-{ts}-{rand}-{suffix}"

            t = Thread.objects.create(title=title, author=user, category=cat, slug=slug_candidate)
            self.stdout.write(self.style.SUCCESS(f"Created thread: {title} (slug={t.slug})"))
            threads.append(t)

        # 4) Пости: по 2 пости на тему (idempotent за допомогою перевірки кількості постів)
        for t in threads:
            existing_count = Post.objects.filter(thread=t).count()
            target = 2
            to_create = max(0, target - existing_count)
            for j in range(to_create):
                content = f"Демо-пост #{existing_count + j + 1} для теми «{t.title}». Текст прикладу — створено автоматично."
                Post.objects.create(thread=t, author=user, content=content)
            if to_create:
                self.stdout.write(self.style.SUCCESS(f"Created {to_create} posts for thread: {t.title}"))
            else:
                self.stdout.write(self.style.WARNING(f"Thread already has {existing_count} posts: {t.title}"))

        # 5) Профілі — впевнюємось, що для кожного існує Profile
        for u in User.objects.all():
            profile, _ = Profile.objects.get_or_create(user=u)
        self.stdout.write(self.style.SUCCESS("Demo data creation completed."))
