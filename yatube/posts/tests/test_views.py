from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from django import forms
import datetime as dt
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, Comment, Follow

User = get_user_model()


class PostPegesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test_slug',
            description='Test description',
        )
        cls.group_2 = Group.objects.create(
            title='Test group 2',
            slug='test_slug_2',
            description='Test description 2',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
            group=cls.group,
            pub_date=dt.datetime(2022, 6, 14, 12, 0, 0),
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Test comment'
        )

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'auth'}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_create'):
                'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/create_post.html',
        }
        for revers_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                responce = self.authorized_client.get(revers_name)
                self.assertTemplateUsed(responce, template)

    def posts_in_pages(self, response):
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        pub_date_0 = first_object.pub_date
        post_title_0 = first_object.group.title
        post_author_0 = first_object.author
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(pub_date_0, self.post.pub_date)
        self.assertEqual(post_title_0, 'Test group')
        self.assertEqual(post_author_0, self.post.author)
        self.assertTrue(post_image_0, self.post.image)

    # Проверка словаря контекста главной страницы
    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.posts_in_pages(response)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}))
        self.posts_in_pages(response)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user}))
        self.posts_in_pages(response)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        object = response.context['post']
        post_text = object.text
        comment = Comment.objects.select_related('post').get(pk=1)
        self.assertEqual(post_text, self.post.text)
        self.assertEqual(comment.text, self.comment.text)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_in_correct_group_page(self):
        """Пост не попал в группу, для которой не был предназначен."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}))
        first_object = response.context['page_obj'][0]
        post_title_0 = first_object.group.title
        self.assertNotEqual(post_title_0, 'Test group 2')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test_slug',
            description='Test description',
        )
        post_list = [
            Post(
                text='Test text',
                pub_date='05.04.2022',
                author=cls.user,
                group=cls.group,
            )
            for _ in range(13)
        ]
        cls.post = Post.objects.bulk_create(post_list)

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_pages_contains_ten_records(self):
        # Проверка: количество постов на первой странице равно 10.
        number_of_posts = {
            reverse('posts:index'): 10,
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}): 10,
            reverse('posts:profile', kwargs={'username': 'auth'}): 10,
        }
        for page, number in number_of_posts.items():
            with self.subTest(number=number):
                response = self.authorized_client.get(page)
                self.assertEqual(len(response.context['page_obj']), number)

    def test_second_pages_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        number_of_posts = {
            reverse('posts:index') + '?page=2': 3,
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}) + (
                '?page=2'): 3,
            reverse('posts:profile', kwargs={'username': 'auth'}) + (
                '?page=2'): 3,
        }
        for page, number in number_of_posts.items():
            with self.subTest(number=number):
                response = self.authorized_client.get(page)
                self.assertEqual(len(response.context['page_obj']), number)


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test_slug',
            description='Test description',
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
            group=cls.group,
            pub_date=dt.datetime(2022, 6, 14, 12, 0, 0),
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index(self):
        """Тест кэширования главной страницыl"""
        response = self.authorized_client.get(reverse('posts:index'))
        post = Post.objects.get(pk=1)
        post.text = 'New text'
        post.save()
        response_2 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, response_2.content)
        cache.clear()
        response_3 = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, response_3.content)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower1 = User.objects.create_user(username='follower1')
        cls.follower2 = User.objects.create_user(username='follower2')
        cls.author = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.author,
        )

    def setUp(self):
        # Создаем авторизованный клиент
        self.follower_client1 = Client()
        self.follower_client1.force_login(self.follower1)
        self.follower_client2 = Client()
        self.follower_client2.force_login(self.follower2)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_follow(self):
        """Тестирование подписки на автора"""
        self.follower_client1.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author},
            ),
        )
        self.assertEqual(Follow.objects.count(), 1)

    def test_unfollow(self):
        """Тестирование отписки от автора"""
        self.follower_client1.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author},
            )
        )
        self.assertEqual(Follow.objects.count(), 1)
        self.follower_client1.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author},
            )
        )
        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_list(self):
        """Тестирование показа записей у подписчика и не подписчика"""
        self.follower_client1.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author},
            )
        )
        self.assertEqual(Follow.objects.count(), 1)
        response = self.follower_client1.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertEqual(post_text_0, self.post.text)
        response = self.follower_client2.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj']
        self.assertFalse(first_object)
