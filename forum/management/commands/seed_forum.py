# forum/management/commands/seed_forum.py
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from forum.models import Category, Thread, Post
from django.utils.text import slugify
from django.utils import timezone


User = get_user_model()

class Command(BaseCommand):
    help = 'Seed forum with demo categories, threads and posts'

    def handle(self, *args, **options):
        # create test user
        user, _ = User.objects.get_or_create(username='testuser', defaults={'email':'test@example.com'})
        if _.__class__.__name__ == 'bool':
            # for Django get_or_create returns (obj, created)
            pass

        # categories
        cats = [
            ('dev', 'Розробка', 'Питання про програмування, фреймворки, поради.'),
            ('general', 'Загальні', 'Обговорення на будь-які теми.'),
            ('life', 'Життя', 'Поради щодо навчання, кар\'єри, мотивації.'),
            ('resources', 'Ресурси', 'Підбірки посилань і матеріалів.'),
        ]
        created_cats = []
        for slug, title, desc in cats:
            c, created = Category.objects.get_or_create(slug=slug, defaults={'title': title, 'description': desc})
            created_cats.append(c)

        # threads
        sample_titles = [
            'Як налаштувати Django + HTMX — короткий гайд',
            'Кращі практики структурування проєкту',
            'Після-екзамена: як не вигоріти',
            'Вибір бази даних для навчального проєкту',
            'Поради по тестуванню коду',
            'Як писати чистий код: чекліст',
            'Початок роботи з Docker для студентів',
            'Оптимізація запитів у Django',
            'Поради для співбесід на позицію junior',
            'Ресурси для вивчення ML'
        ]

        threads = []
        for i, title in enumerate(sample_titles):
            cat = random.choice(created_cats)
            t, created = Thread.objects.get_or_create(
                title=title,
                author=user,
                category=cat,
                defaults={'slug': f'{slugify(title)[:50]}-{i}-{int(timezone.now().timestamp())}'}
            )
            threads.append(t)

        # posts
        lorem = "Це тестовий пост для демонстрації інтерфейсу. " \
                "Тут може бути докладний опис проблеми або запитання."
        for t in threads:
            # 1..3 posts per thread
            for j in range(random.randint(1,3)):
                Post.objects.create(thread=t, author=user, content=f"{lorem} (thread: {t.title}, post #{j+1})")

        self.stdout.write(self.style.SUCCESS('Seed completed: categories, threads, posts, testuser'))
